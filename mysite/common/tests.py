"""
common/utils.py のユニットテスト
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from common.utils import safe_redirect, LikedPostMixin
from post.models import Post

User = get_user_model()


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def make_user(username='testuser', email='test@example.com', password='pass1234!'):
    return User.objects.create_user(username=username, email=email, password=password)


def make_post(author, content='テスト投稿'):
    return Post.objects.create(author=author, content=content)


# ---------------------------------------------------------------------------
# safe_redirect
# ---------------------------------------------------------------------------

class SafeRedirectTest(TestCase):
    """safe_redirect のオープンリダイレクト防止ロジックのテスト。"""

    def _make_request(self, referer=None):
        factory = RequestFactory()
        request = factory.get('/')
        if referer:
            request.META['HTTP_REFERER'] = referer
        request.META.setdefault('SERVER_NAME', 'testserver')
        request.META.setdefault('SERVER_PORT', '80')
        return request

    def test_referer_なし_fallback_へリダイレクト(self):
        request = self._make_request()
        response = safe_redirect(request, fallback='post:post_list')
        self.assertEqual(response.status_code, 302)
        # Django の redirect() は URL 名を解決した絶対パスを返す
        self.assertEqual(response['Location'], '/')

    def test_同一ホストのreferer_元ページへリダイレクト(self):
        request = self._make_request(referer='http://testserver/some/page/')
        response = safe_redirect(request, fallback='post:post_list')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/some/page/')

    def test_外部ドメインのreferer_fallbackへリダイレクト(self):
        """オープンリダイレクト防止: 外部サイトには遷移しない。"""
        request = self._make_request(referer='http://evil.example.com/malicious/')
        response = safe_redirect(request, fallback='post:post_list')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.example.com', response['Location'])

    def test_fallback引数が反映される(self):
        request = self._make_request()
        response = safe_redirect(request, fallback='accounts:login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


# ---------------------------------------------------------------------------
# LikedPostMixin
# ---------------------------------------------------------------------------

class LikedPostMixinTest(TestCase):
    """LikedPostMixin のユニットテスト。"""

    def setUp(self):
        self.user = make_user()
        self.other = make_user(username='other', email='other@example.com')
        self.post1 = make_post(self.other, content='投稿1')
        self.post2 = make_post(self.other, content='投稿2')
        self.post1.liked_users.add(self.user)  # user は post1 だけいいね

    def _make_request(self, user):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        return request

    def _make_mixin(self, user):
        mixin = LikedPostMixin()
        mixin.request = self._make_request(user)
        return mixin

    def test_認証済みユーザーのliked_post_ids取得(self):
        mixin = self._make_mixin(self.user)
        ids = mixin.get_liked_post_ids()
        self.assertIn(self.post1.pk, ids)
        self.assertNotIn(self.post2.pk, ids)

    def test_未認証ユーザーはliked_post_ids空セット(self):
        mixin = LikedPostMixin()
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        mixin.request = request
        ids = mixin.get_liked_post_ids()
        self.assertEqual(ids, set())

    def test_build_post_zip_いいね済みならTrue(self):
        mixin = self._make_mixin(self.user)
        post_list = [self.post1, self.post2]
        result = list(mixin.build_post_zip(post_list))
        self.assertEqual(result[0], (self.post1, True))
        self.assertEqual(result[1], (self.post2, False))

    def test_build_post_zip_liked_post_ids明示指定(self):
        mixin = self._make_mixin(self.user)
        post_list = [self.post1]
        result = list(mixin.build_post_zip(post_list, liked_post_ids=set()))
        self.assertEqual(result[0], (self.post1, False))

    def test_annotate_post_qs_カウントフィールドが追加される(self):
        from django.db.models import QuerySet
        mixin = self._make_mixin(self.user)
        qs = Post.objects.all()
        annotated = mixin.annotate_post_qs(qs)
        post = annotated.get(pk=self.post1.pk)
        self.assertEqual(post.liked_count, 1)
        self.assertEqual(post.reply_count, 0)
        self.assertEqual(post.repost_count, 0)
