from django.shortcuts import redirect, render, get_object_or_404

from boards.models import Comments, Themes
from . import forms
from django.contrib import messages
from django.http import Http404
from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Q

# 主題作成フォーム
def create_theme(request):
    create_theme_form = forms.CreateThemeForm(request.POST or None)
    if create_theme_form.is_valid():
        if not request.user.is_authenticated:  # 承認されてないならエラー
            raise Http404
        create_theme_form.instance.user = request.user
        create_theme_form.save()
        messages.success(request, "掲示板を作成しました。")
        return redirect("boards:list_themes")
    return render(
        request,
        "boards/create_theme.html",
        context={
            "create_theme_form": create_theme_form,
        },
    )


# 投稿一覧表示
def list_themes(request):
    themes = Themes.objects.fetch_all_themes()
    # 検索機能
    search_word = request.GET.get("search_word")
    if search_word:
        themes = themes.filter(Q(title__icontains=search_word))
        messages.success(request, f"「{search_word}」の検索結果")
    return render(
        request,
        "boards/list_themes.html",
        context={
            "themes": themes,
        },
    )


def edit_theme(request, id):
    theme = get_object_or_404(Themes, id=id)
    # 投稿者と異なる場合エラー
    if theme.user.id != request.user.id:
        raise Http404
    edit_theme_form = forms.CreateThemeForm(request.POST or None, instance=theme)
    if edit_theme_form.is_valid():
        edit_theme_form.save()
        messages.success(request, "掲示板変更")
        return redirect("boards:list_themes")
    return render(
        request,
        "boards/edit_theme.html",
        context={
            "edit_theme_form": edit_theme_form,
            "id": id,
        },
    )


# 削除処理
def delete_theme(request, id):
    theme = get_object_or_404(Themes, id=id)
    if theme.user.id != request.user.id:
        raise Http404
    delete_theme_form = forms.DeleteThemeForm(request.POST or None)
    if delete_theme_form.is_valid():
        theme.delete()
        messages.success(request, "掲示板を削除しました")
        return redirect("boards:list_themes")
    return render(
        request,
        "boards/delete_theme.html",
        context={
            "delete_theme_form": delete_theme_form,
        },
    )


# コメント投稿
def post_comments(request, theme_id):
    post_comment_form = forms.PostCommentForm(request.POST or None)
    theme = get_object_or_404(Themes, id=theme_id)
    comments = Comments.objects.fetch_by_theme_id(theme_id)
    if post_comment_form.is_valid():
        post_comment_form.instance.theme = theme
        post_comment_form.instance.user = request.user
        post_comment_form.save()
        return redirect("boards:post_comments", theme_id=theme_id)
    return render(
        request,
        "boards/post_comments.html",
        context={
            "post_comment_form": post_comment_form,
            "theme": theme,
            "comments": comments,
        },
    )


# コメント一時保存機能
def save_comment(request):
    if request.is_ajax:
        comment = request.GET.get("comment")
        theme_id = request.GET.get("theme_id")
        if comment and theme_id:
            cache.set(
                f"saved_comment-theme_id={theme_id}-user_id={request.use.id}", comment
            )
            return JsonResponse({"message": "一時保存"})
