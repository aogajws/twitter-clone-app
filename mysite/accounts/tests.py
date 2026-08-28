"""
accounts アプリのテスト

カバー範囲:
  - User モデル（UserManager・フィールド・フォロー関係）
  - accounts フォーム（LoginForm, CustomUserCreationForm, UserChangeForm）
  - accounts ビュー（認証・プロフィール・フォロー・ユーザー一覧）
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.forms import (
    CustomUserCreationForm,
    UserChangeForm,
    UploadProfileImgForm,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def make_user(username='alice', email='alice@example.com', password='StrongPass1!'):
    return User.objects.create_user(username=username, email=email, password=password)


# ===========================================================================
# モデルテスト
# ===========================================================================

class UserManagerTest(TestCase):
    """UserManager._create_user のバリデーションテスト。"""

    def test_create_user_正常系(self):
        user = User.objects.create_user(
            username='bob', email='bob@example.com', password='pass1234!'
        )
        self.assertEqual(user.username, 'bob')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('pass1234!'))

    def test_create_user_username空でValueError(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username='', email='x@example.com', password='pass')

    def test_create_user_email空でValueError(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username='bob', email='', password='pass')

    def test_create_superuser_is_staff_True(self):
        su = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='pass1234!'
        )
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)

    def test_create_superuser_is_staff_False_でValueError(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                username='admin', email='admin@example.com',
                password='pass', is_staff=False
            )

    def test_create_superuser_is_superuser_False_でValueError(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                username='admin', email='admin@example.com',
                password='pass', is_superuser=False
            )


class UserModelTest(TestCase):
    """User モデルのフィールド・メソッドテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')

    def test_str_はusernameを返す(self):
        self.assertEqual(str(self.alice), 'alice')

    def test_introduction_のデフォルト値は空文字(self):
        self.assertEqual(self.alice.introduction, '')

    def test_follow_するとfollowersに追加される(self):
        # alice が bob をフォロー
        self.bob.followers.add(self.alice)
        self.assertIn(self.alice, self.bob.followers.all())
        # alice.following から bob が見える
        self.assertIn(self.bob, self.alice.following.all())

    def test_remove_するとfollowersから削除される(self):
        self.bob.followers.add(self.alice)
        self.bob.followers.remove(self.alice)
        self.assertNotIn(self.alice, self.bob.followers.all())

    def test_follower_count(self):
        self.bob.followers.add(self.alice)
        self.assertEqual(self.bob.followers.count(), 1)

    def test_following_count(self):
        self.bob.followers.add(self.alice)
        self.assertEqual(self.alice.following.count(), 1)


# ===========================================================================
# フォームテスト
# ===========================================================================

class CustomUserCreationFormTest(TestCase):
    """ユーザー登録フォームのバリデーションテスト。"""

    def _valid_data(self, **kwargs):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass1!',
            'password2': 'StrongPass1!',
        }
        data.update(kwargs)
        return data

    def test_正常なデータでvalidになる(self):
        form = CustomUserCreationForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_email未入力でinvalid(self):
        form = CustomUserCreationForm(data=self._valid_data(email=''))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_パスワード不一致でinvalid(self):
        form = CustomUserCreationForm(
            data=self._valid_data(password1='StrongPass1!', password2='different')
        )
        self.assertFalse(form.is_valid())

    def test_フィールドにplaceholderとclassが設定される(self):
        form = CustomUserCreationForm()
        for field in form.fields.values():
            self.assertEqual(field.widget.attrs.get('class'), 'form-control')
            self.assertIn('placeholder', field.widget.attrs)


class UserChangeFormTest(TestCase):
    """プロフィール編集フォームのバリデーション・updateメソッドテスト。"""

    def setUp(self):
        self.user = make_user()

    def _bound_form(self, **kwargs):
        data = {
            'username': self.user.username,
            'email': self.user.email,
            'introduction': self.user.introduction,
        }
        data.update(kwargs)
        return UserChangeForm(data=data, username=self.user.username)

    def test_変更なしのデータでvalidになる(self):
        form = self._bound_form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_update_変更なしの場合はDBアクセスしない(self):
        form = self._bound_form()
        form.is_valid()
        original_username = self.user.username
        form.update(self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, original_username)

    def test_update_usernameのみ変更する(self):
        form = self._bound_form(username='alice_new')
        self.assertTrue(form.is_valid(), form.errors)
        form.update(self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alice_new')

    def test_update_emailのみ変更する(self):
        form = self._bound_form(email='new@example.com')
        self.assertTrue(form.is_valid(), form.errors)
        form.update(self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

    def test_update_introductionのみ変更する(self):
        form = self._bound_form(introduction='こんにちは')
        self.assertTrue(form.is_valid(), form.errors)
        form.update(self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.introduction, 'こんにちは')

    def test_フォームのinitial値が既存userから取得される(self):
        form = UserChangeForm(username=self.user.username)
        # instance がセットされ、初期値が正しく入っている
        self.assertEqual(form.instance.pk, self.user.pk)


# ===========================================================================
# ビューテスト
# ===========================================================================

class LoginViewTest(TestCase):
    """ログイン・ログアウトビューのテスト。"""

    def setUp(self):
        self.user = make_user()
        self.client = Client()

    def test_ログインページ_200を返す(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_正しい認証情報でログイン成功後リダイレクト(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'alice',
            'password': 'StrongPass1!',
        })
        self.assertEqual(response.status_code, 302)

    def test_誤った認証情報でログイン失敗(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'alice',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)  # フォームを再表示
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserCreateViewTest(TestCase):
    """ユーザー登録ビューのテスト。"""

    def test_登録ページ_200を返す(self):
        response = self.client.get(reverse('accounts:create'))
        self.assertEqual(response.status_code, 200)

    def test_正常登録後post_listへリダイレクトしログイン済みになる(self):
        response = self.client.post(reverse('accounts:create'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass1!',
            'password2': 'StrongPass1!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('post:post_list'))
        # セッションにユーザーが記録されている = ログイン済み
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_メール重複で登録失敗(self):
        make_user(username='existing', email='dup@example.com')
        response = self.client.post(reverse('accounts:create'), {
            'username': 'newuser',
            'email': 'dup@example.com',
            'password1': 'StrongPass1!',
            'password2': 'StrongPass1!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class LoginRequiredViewsTest(TestCase):
    """@login_required / LoginRequiredMixin が機能しているかのテスト。"""

    LOGIN_URL = '/accounts/login/'

    def assertRedirectsToLogin(self, url, method='get', data=None):
        fn = getattr(self.client, method)
        response = fn(url, data or {})
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_未ログインでeditはloginへリダイレクト(self):
        self.assertRedirectsToLogin(reverse('accounts:edit'))

    def test_未ログインでpasswordはloginへリダイレクト(self):
        self.assertRedirectsToLogin(reverse('accounts:password'))

    def test_未ログインでiconはloginへリダイレクト(self):
        self.assertRedirectsToLogin(reverse('accounts:icon'))

    def test_未ログインでsearch_accountsはloginへリダイレクト(self):
        self.assertRedirectsToLogin(reverse('accounts:search_accounts'))


class UserProfileViewTest(TestCase):
    """user_profile_view のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.client = Client()

    def test_プロフィールページ_200を返す_未ログイン(self):
        response = self.client.get(reverse('accounts:profile', args=['alice']))
        self.assertEqual(response.status_code, 200)

    def test_存在しないユーザーで404(self):
        response = self.client.get(reverse('accounts:profile', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)

    def test_フォロー中かどうかがコンテキストに反映される(self):
        self.client.force_login(self.alice)
        self.bob.followers.add(self.alice)  # alice が bob をフォロー
        response = self.client.get(reverse('accounts:profile', args=['bob']))
        self.assertTrue(response.context['is_following'])

    def test_フォローしていない場合is_following_False(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('accounts:profile', args=['bob']))
        self.assertFalse(response.context['is_following'])

    def test_follower_count_following_countがコンテキストに含まれる(self):
        self.bob.followers.add(self.alice)
        response = self.client.get(reverse('accounts:profile', args=['bob']))
        self.assertEqual(response.context['follower_count'], 1)
        self.assertEqual(response.context['following_count'], 0)


class FollowViewTest(TestCase):
    """follow_view / remove_view のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_follow_POSTでフォロー関係が追加される(self):
        self.client.post(reverse('accounts:follow', args=['bob']))
        self.assertIn(self.alice, self.bob.followers.all())

    def test_remove_POSTでフォロー関係が削除される(self):
        self.bob.followers.add(self.alice)
        self.client.post(reverse('accounts:remove', args=['bob']))
        self.assertNotIn(self.alice, self.bob.followers.all())

    def test_follow_GETは405を返す(self):
        response = self.client.get(reverse('accounts:follow', args=['bob']))
        self.assertEqual(response.status_code, 405)

    def test_remove_GETは405を返す(self):
        response = self.client.get(reverse('accounts:remove', args=['bob']))
        self.assertEqual(response.status_code, 405)

    def test_未ログインでfollow_はloginへリダイレクト(self):
        self.client.logout()
        response = self.client.post(reverse('accounts:follow', args=['bob']))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_存在しないユーザーへのfollow_は404(self):
        response = self.client.post(reverse('accounts:follow', args=['nobody']))
        self.assertEqual(response.status_code, 404)


class AccountsListViewTest(TestCase):
    """ユーザー一覧・フォロー一覧ビューのテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.carol = make_user(username='carol', email='carol@example.com')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_ユーザー一覧_200を返す(self):
        response = self.client.get(reverse('accounts:search_accounts'))
        self.assertEqual(response.status_code, 200)

    def test_ユーザー一覧_全ユーザーが含まれる(self):
        response = self.client.get(reverse('accounts:search_accounts'))
        usernames = [u.username for u in response.context['object_list']]
        self.assertIn('alice', usernames)
        self.assertIn('bob', usernames)

    def test_ユーザー一覧_クエリで絞り込める(self):
        response = self.client.get(reverse('accounts:search_accounts'), {'query': 'bob'})
        usernames = [u.username for u in response.context['object_list']]
        self.assertIn('bob', usernames)
        self.assertNotIn('alice', usernames)

    def test_フォロー一覧_フォロー中ユーザーのみ表示(self):
        self.bob.followers.add(self.alice)  # alice → bob をフォロー
        response = self.client.get(reverse('accounts:followings', args=['alice']))
        usernames = [u.username for u in response.context['object_list']]
        self.assertIn('bob', usernames)
        self.assertNotIn('carol', usernames)

    def test_フォロワー一覧_フォロワーのみ表示(self):
        self.alice.followers.add(self.bob)  # bob → alice をフォロー
        response = self.client.get(reverse('accounts:followers', args=['alice']))
        usernames = [u.username for u in response.context['object_list']]
        self.assertIn('bob', usernames)
        self.assertNotIn('carol', usernames)
