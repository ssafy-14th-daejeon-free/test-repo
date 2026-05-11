from django import forms

from .models import Comment, Post, Tag


class PostForm(forms.ModelForm):
    tags_text = forms.CharField(
        label="Tags",
        required=False,
        help_text="Separate up to 8 tags with commas.",
    )
    series_title = forms.CharField(
        label="Series",
        required=False,
        help_text="Optional series title to group related posts.",
    )

    class Meta:
        model = Post
        fields = (
            "title",
            "cover_url",
            "content",
            "excerpt",
            "series_title",
            "tags_text",
            "is_public",
        )
        labels = {
            "title": "Title",
            "cover_url": "Cover image URL",
            "content": "Content",
            "excerpt": "Excerpt",
            "is_public": "Public",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Title"}),
            "cover_url": forms.URLInput(attrs={"placeholder": "https://example.com/image.jpg"}),
            "content": forms.Textarea(
                attrs={
                    "rows": 18,
                    "placeholder": "Write with Markdown.",
                }
            ),
            "excerpt": forms.TextInput(attrs={"placeholder": "Short summary for cards"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )
            if self.instance.series:
                self.fields["series_title"].initial = self.instance.series.title

    def clean_tags_text(self):
        raw = self.cleaned_data["tags_text"]
        tag_names = []
        for name in [part.strip() for part in raw.split(",") if part.strip()]:
            if name not in tag_names:
                tag_names.append(name)

        if len(tag_names) > 8:
            raise forms.ValidationError("Use up to 8 tags.")

        too_long = [name for name in tag_names if len(name) > 30]
        if too_long:
            raise forms.ValidationError("Each tag must be 30 characters or fewer.")

        return tag_names

    def save_tags(self, post):
        tags = []
        for name in self.cleaned_data["tags_text"]:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        post.tags.set(tags)

    def save_series(self, post):
        title = self.cleaned_data["series_title"].strip()
        if not title:
            post.series = None
            post.save(update_fields=["series"])
            return

        series, _ = post.author.series.get_or_create(title=title)
        if post.series_id != series.pk:
            post.series = series
            post.save(update_fields=["series"])


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        labels = {"content": "Comment"}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Write a comment.",
                }
            )
        }
