from django import forms

from .models import Post, Tag


class PostForm(forms.ModelForm):
    tags_text = forms.CharField(
        label="태그",
        required=False,
        help_text="쉼표로 구분해 최대 8개까지 입력하세요.",
    )

    class Meta:
        model = Post
        fields = ("title", "content", "excerpt", "tags_text", "is_public")
        labels = {
            "title": "제목",
            "content": "본문",
            "excerpt": "요약",
            "is_public": "공개",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "제목을 입력하세요"}),
            "content": forms.Textarea(
                attrs={
                    "rows": 18,
                    "placeholder": "Markdown으로 글을 작성하세요.",
                }
            ),
            "excerpt": forms.TextInput(attrs={"placeholder": "목록에 표시할 짧은 요약"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_tags_text(self):
        raw = self.cleaned_data["tags_text"]
        tag_names = []
        for name in [part.strip() for part in raw.split(",") if part.strip()]:
            if name not in tag_names:
                tag_names.append(name)

        if len(tag_names) > 8:
            raise forms.ValidationError("태그는 최대 8개까지 입력할 수 있습니다.")

        too_long = [name for name in tag_names if len(name) > 30]
        if too_long:
            raise forms.ValidationError("태그 이름은 30자를 넘을 수 없습니다.")

        return tag_names

    def save_tags(self, post):
        tags = []
        for name in self.cleaned_data["tags_text"]:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        post.tags.set(tags)
