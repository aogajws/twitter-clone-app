"""
プロジェクト共通のユーティリティ関数・Mixin
"""
from django.shortcuts import redirect
from django.db.models import Count


def safe_redirect(request, fallback='post:post_list'):
    """
    HTTP_REFERER が存在しない場合やオープンリダイレクトを防ぎ、安全にリダイレクトする。
    同一ホストへのリダイレクトのみ許可し、それ以外は fallback URL に遷移する。
    """
    referer = request.META.get('HTTP_REFERER', '')
    host = request.get_host()
    if referer and host in referer:
        return redirect(referer)
    return redirect(fallback)


class LikedPostMixin:
    """
    投稿一覧ビューで「いいね済み投稿IDセット」を一括取得して
    context['zip'] に (post, liked: bool) のペアを格納する共通 Mixin。

    使用する ListView は get_queryset() で Post オブジェクトを返すこと。
    """

    def get_liked_post_ids(self):
        user = self.request.user
        if not user.is_authenticated:
            return set()
        return set(user.favorite_posts.values_list('pk', flat=True))

    def build_post_zip(self, post_list, liked_post_ids=None):
        if liked_post_ids is None:
            liked_post_ids = self.get_liked_post_ids()
        return zip(
            post_list,
            [post.pk in liked_post_ids for post in post_list],
        )

    def annotate_post_qs(self, qs):
        """liked_count / reply_count / repost_count を annotate して返す。"""
        return qs.annotate(
            liked_count=Count('liked_users'),
            reply_count=Count('replies'),
            repost_count=Count('reposted'),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_list = context['object_list']
        context['zip'] = self.build_post_zip(post_list)
        return context
