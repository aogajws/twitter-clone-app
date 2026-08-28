"""
post アプリのテスト

カバー範囲:
  - Post モデル（フィールド・__str__・ordering・CASCADE/SET_NULL）
  - PostCreationForm のバリデーション
  - post ビュー（タイムライン・作成・いいね・削除・検索・詳細・返信・リツイート）
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from post.models import Post
from post.forms import PostCreationForm

User = get_user_model()


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def make_user(username='alice', email='alice@example.com', password='StrongPass1!'):
    return User.objects.create_user(username=username, email=email, password=password)


def make_post(author, content='テスト投稿', parent=None, repost_parent=None):
    return Post.objects.create(
        author=author,
        content=content,
        parent=parent,
        repost_parent=repost_parent,
    )


# ===========================================================================
# モデルテスト
# ===========================================================================

class PostModelTest(TestCase):
    """Post モデルのフィールド・メソッド・挙動テスト。"""

    def setUp(self):
        self.alice = make_user()

    def test_str_は50文字で切り詰められる(self):
        long_content = 'あ' * 60
        post = make_post(self.alice, content=long_content)
        self.assertEqual(str(post), 'あ' * 50)

    def test_str_が50文字以下ならそのまま返す(self):
        post = make_post(self.alice, content='短い投稿')
        self.assertEqual(str(post), '短い投稿')

    def test_ordering_で新しい投稿が先頭になる(self):
        post1 = make_post(self.alice, content='1つ目')
        post2 = make_post(self.alice, content='2つ目')
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], post2)  # 新しい方が先
        self.assertEqual(posts[1], post1)

    def test_author削除でPostもCASCADE削除される(self):
        bob = make_user(username='bob', email='bob@example.com')
        post = make_post(bob)
        bob.delete()
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_parent削除で返信のparentはNullになる(self):
        parent_post = make_post(self.alice, content='親投稿')
        reply = make_post(self.alice, content='返信', parent=parent_post)
        parent_post.delete()
        reply.refresh_from_db()
        self.assertIsNone(reply.parent)

    def test_repost_parent削除でリツイートのrepost_parentはNullになる(self):
        original = make_post(self.alice, content='元投稿')
        repost = make_post(self.alice, content='RT', repost_parent=original)
        original.delete()
        repost.refresh_from_db()
        self.assertIsNone(repost.repost_parent)

    def test_liked_users_追加と削除(self):
        bob = make_user(username='bob', email='bob@example.com')
        post = make_post(self.alice)
        post.liked_users.add(bob)
        self.assertIn(bob, post.liked_users.all())
        post.liked_users.remove(bob)
        self.assertNotIn(bob, post.liked_users.all())

    def test_replies_related_name(self):
        parent = make_post(self.alice, content='親')
        reply = make_post(self.alice, content='返信', parent=parent)
        self.assertIn(reply, parent.replies.all())

    def test_reposted_related_name(self):
        original = make_post(self.alice, content='元')
        repost = make_post(self.alice, content='RT', repost_parent=original)
        self.assertIn(repost, original.reposted.all())


# ===========================================================================
# フォームテスト
# ===========================================================================

class PostCreationFormTest(TestCase):
    """PostCreationForm のバリデーションテスト。"""

    def test_contentあり_validになる(self):
        form = PostCreationForm(data={'content': 'テスト'})
        self.assertTrue(form.is_valid())

    def test_content空_invalidになる(self):
        form = PostCreationForm(data={'content': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_ウィジェットにmaxlength属性が設定される(self):
        form = PostCreationForm()
        widget_attrs = form.fields['content'].widget.attrs
        self.assertIn('maxlength', widget_attrs)
        self.assertEqual(int(widget_attrs['maxlength']), 280)

    def test_ウィジェットにplaceholderとclassが設定される(self):
        form = PostCreationForm()
        attrs = form.fields['content'].widget.attrs
        self.assertEqual(attrs.get('class'), 'form-control')
        self.assertIn('placeholder', attrs)


# ===========================================================================
# ビューテスト
# ===========================================================================

class PostListViewTest(TestCase):
    """PostListView（タイムライン）のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.carol = make_user(username='carol', email='carol@example.com')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.get(reverse('post:post_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_自分の投稿が表示される(self):
        post = make_post(self.alice, content='自分の投稿')
        response = self.client.get(reverse('post:post_list'))
        # context['zip'] はテンプレートで消費済みなので object_list から確認する
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(post.pk, post_ids)

    def test_フォロー中ユーザーの投稿が表示される(self):
        self.bob.followers.add(self.alice)  # alice → bob をフォロー
        post = make_post(self.bob, content='bobの投稿')
        response = self.client.get(reverse('post:post_list'))
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(post.pk, post_ids)

    def test_フォロー外ユーザーの投稿は表示されない(self):
        post = make_post(self.carol, content='carolの投稿')  # alice はフォローしていない
        response = self.client.get(reverse('post:post_list'))
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertNotIn(post.pk, post_ids)


class PostCreateViewTest(TestCase):
    """PostCreateView のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.client = Client()
        self.client.force_login(self.alice)

    def test_GET_200を返す(self):
        response = self.client.get(reverse('post:post_create'))
        self.assertEqual(response.status_code, 200)

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.get(reverse('post:post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_POST成功で投稿が作成されpost_listへリダイレクト(self):
        response = self.client.post(reverse('post:post_create'), {'content': '新しいツイート'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(content='新しいツイート', author=self.alice).exists())

    def test_投稿者がログインユーザーになる(self):
        self.client.post(reverse('post:post_create'), {'content': 'テスト'})
        post = Post.objects.get(content='テスト')
        self.assertEqual(post.author, self.alice)

    def test_空contentで投稿失敗(self):
        self.client.post(reverse('post:post_create'), {'content': ''})
        self.assertFalse(Post.objects.filter(author=self.alice).exists())


class FavoriteViewTest(TestCase):
    """favorite_view（いいねトグル）のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.post = make_post(self.bob)
        self.client = Client()
        self.client.force_login(self.alice)

    def test_いいねが追加される(self):
        self.client.post(reverse('post:favorite', args=[self.post.pk]))
        self.assertIn(self.alice, self.post.liked_users.all())

    def test_いいね済みの場合いいねが取り消される(self):
        self.post.liked_users.add(self.alice)
        self.client.post(reverse('post:favorite', args=[self.post.pk]))
        self.assertNotIn(self.alice, self.post.liked_users.all())

    def test_GETリクエストは405を返す(self):
        response = self.client.get(reverse('post:favorite', args=[self.post.pk]))
        self.assertEqual(response.status_code, 405)

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.post(reverse('post:favorite', args=[self.post.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_存在しない投稿は404を返す(self):
        response = self.client.post(reverse('post:favorite', args=[9999]))
        self.assertEqual(response.status_code, 404)


class DeleteViewTest(TestCase):
    """delete_view のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_自分の投稿を削除できる(self):
        post = make_post(self.alice)
        self.client.post(reverse('post:delete', args=[post.pk]))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_他人の投稿は削除されない(self):
        post = make_post(self.bob)
        self.client.post(reverse('post:delete', args=[post.pk]))
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_GETリクエストは405を返す(self):
        post = make_post(self.alice)
        response = self.client.get(reverse('post:delete', args=[post.pk]))
        self.assertEqual(response.status_code, 405)

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        post = make_post(self.alice)
        response = self.client.post(reverse('post:delete', args=[post.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


class SearchPostListViewTest(TestCase):
    """SearchPostListView のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.client = Client()
        self.client.force_login(self.alice)
        self.post1 = make_post(self.alice, content='Djangoは楽しい')
        self.post2 = make_post(self.alice, content='Pythonも楽しい')
        self.post3 = make_post(self.alice, content='Goが速い')

    def test_クエリなしで全件返す(self):
        response = self.client.get(reverse('post:search'))
        self.assertEqual(response.status_code, 200)
        # object_list から確認（zip は消費済みのため）
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(self.post1.pk, post_ids)
        self.assertIn(self.post2.pk, post_ids)
        self.assertIn(self.post3.pk, post_ids)

    def test_クエリで絞り込める(self):
        response = self.client.get(reverse('post:search'), {'query': 'Django'})
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(self.post1.pk, post_ids)
        self.assertNotIn(self.post3.pk, post_ids)

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.get(reverse('post:search'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


class PostStatusViewTest(TestCase):
    """PostStatusView のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.post = make_post(self.alice, content='詳細表示テスト')
        self.client = Client()

    def test_未ログインでも200を返す(self):
        response = self.client.get(reverse('post:status', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)

    def test_存在しない投稿は404を返す(self):
        response = self.client.get(reverse('post:status', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_liked_コンテキストがFalse_未ログイン(self):
        response = self.client.get(reverse('post:status', args=[self.post.pk]))
        self.assertFalse(response.context['liked'])

    def test_liked_コンテキストがTrue_いいね済み(self):
        self.client.force_login(self.bob)
        self.post.liked_users.add(self.bob)
        response = self.client.get(reverse('post:status', args=[self.post.pk]))
        self.assertTrue(response.context['liked'])

    def test_likesカウントがコンテキストに含まれる(self):
        self.post.liked_users.add(self.alice)
        response = self.client.get(reverse('post:status', args=[self.post.pk]))
        self.assertEqual(response.context['likes'], 1)

    def test_parent_postがコンテキストに含まれる(self):
        self.client.force_login(self.alice)
        reply = make_post(self.alice, content='返信', parent=self.post)
        response = self.client.get(reverse('post:status', args=[reply.pk]))
        self.assertEqual(response.context['parent_post'], self.post)

    def test_parent_postなしのときNone(self):
        response = self.client.get(reverse('post:status', args=[self.post.pk]))
        self.assertIsNone(response.context['parent_post'])


class ReplyCreateViewTest(TestCase):
    """reply_create_view のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.original = make_post(self.bob, content='元投稿')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_GET_200を返す(self):
        response = self.client.get(reverse('post:reply', args=[self.original.pk]))
        self.assertEqual(response.status_code, 200)

    def test_返信作成_parentが元投稿に設定される(self):
        self.client.post(reverse('post:reply', args=[self.original.pk]), {
            'content': '返信テキスト',
        })
        reply = Post.objects.filter(parent=self.original).first()
        self.assertIsNotNone(reply)
        self.assertEqual(reply.parent, self.original)

    def test_返信作成_contentに元投稿者へのメンションが付与される(self):
        self.client.post(reverse('post:reply', args=[self.original.pk]), {
            'content': '返信テキスト',
        })
        reply = Post.objects.filter(parent=self.original).first()
        self.assertTrue(reply.content.startswith(f'@{self.bob.username}'))

    def test_返信作成後post_listへリダイレクト(self):
        response = self.client.post(reverse('post:reply', args=[self.original.pk]), {
            'content': '返信テキスト',
        })
        self.assertRedirects(response, reverse('post:post_list'))

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.get(reverse('post:reply', args=[self.original.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_空contentでは返信が作成されない(self):
        self.client.post(reverse('post:reply', args=[self.original.pk]), {'content': ''})
        self.assertFalse(Post.objects.filter(parent=self.original).exists())


class RepostCreateViewTest(TestCase):
    """repost_create_view のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.original = make_post(self.bob, content='元投稿')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_GET_200を返す(self):
        response = self.client.get(reverse('post:repost', args=[self.original.pk]))
        self.assertEqual(response.status_code, 200)

    def test_リツイート作成_repost_parentが元投稿に設定される(self):
        self.client.post(reverse('post:repost', args=[self.original.pk]), {
            'content': 'RTコメント',
        })
        repost = Post.objects.filter(repost_parent=self.original).first()
        self.assertIsNotNone(repost)
        self.assertEqual(repost.repost_parent, self.original)

    def test_リツイート作成後post_listへリダイレクト(self):
        response = self.client.post(reverse('post:repost', args=[self.original.pk]), {
            'content': 'RTコメント',
        })
        self.assertRedirects(response, reverse('post:post_list'))

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.get(reverse('post:repost', args=[self.original.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


class ReplyPostListViewTest(TestCase):
    """ReplyPostListView（自分へのメンション一覧）のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.client = Client()
        self.client.force_login(self.alice)

    def test_半角スペース付きメンションがヒットする(self):
        post = make_post(self.bob, content=f'@{self.alice.username} こんにちは')
        response = self.client.get(reverse('post:replies'))
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(post.pk, post_ids)

    def test_全角スペース付きメンションがヒットする(self):
        post = make_post(self.bob, content=f'@{self.alice.username}\u3000こんにちは')
        response = self.client.get(reverse('post:replies'))
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(post.pk, post_ids)

    def test_末尾メンションがヒットする(self):
        post = make_post(self.bob, content=f'@{self.alice.username}')
        response = self.client.get(reverse('post:replies'))
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertIn(post.pk, post_ids)

    def test_別ユーザーへのメンションはヒットしない(self):
        post = make_post(self.bob, content=f'@{self.bob.username} 自分へ')
        response = self.client.get(reverse('post:replies'))
        post_ids = [p.pk for p in response.context['object_list']]
        self.assertNotIn(post.pk, post_ids)

    def test_未ログインはloginへリダイレクト(self):
        self.client.logout()
        response = self.client.get(reverse('post:replies'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


class LikedAccountsListViewTest(TestCase):
    """LikedAccountsListView（いいねしたユーザー一覧）のテスト。"""

    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(username='bob', email='bob@example.com')
        self.post = make_post(self.alice)
        self.client = Client()
        self.client.force_login(self.alice)

    def test_200を返す(self):
        response = self.client.get(reverse('post:favorited', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)

    def test_いいねしたユーザーが一覧に含まれる(self):
        self.post.liked_users.add(self.bob)
        response = self.client.get(reverse('post:favorited', args=[self.post.pk]))
        usernames = [u.username for u in response.context['object_list']]
        self.assertIn('bob', usernames)

    def test_いいねしていないユーザーは含まれない(self):
        response = self.client.get(reverse('post:favorited', args=[self.post.pk]))
        usernames = [u.username for u in response.context['object_list']]
        self.assertNotIn('bob', usernames)
