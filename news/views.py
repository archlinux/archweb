from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView

from .models import News
from main.utils import find_unique_slug, parse_markdown


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        exclude = ('id', 'slug', 'author', 'postdate', 'safe_mode')


class NewsDetailView(DetailView):
    queryset = News.objects.all().select_related('author')
    template_name = "news/view.html"


class NewsListView(ListView):
    queryset = News.objects.all().select_related('author').defer('content')
    template_name = "news/list.html"
    paginate_by = 50


class NewsCreateView(CreateView):
    model = News
    form_class = NewsForm
    template_name = "news/add.html"

    def form_valid(self, form):
        # special logic, we auto-fill the author and slug fields
        newsitem = form.save(commit=False)
        newsitem.author = self.request.user
        newsitem.slug = find_unique_slug(News, newsitem.title)
        newsitem.save()
        if newsitem.send_announce:
            ctx = {
                'news': newsitem,
            }
            headers = dict()
            if settings.MAILMAN_PASSWORD:
                headers['Approved'] = settings.MAILMAN_PASSWORD
            template = loader.get_template('news/news_email_notification.txt')
            EmailMessage(
                subject=f'[arch-announce] {newsitem.title}',
                body=template.render(ctx),
                from_email=f'Arch Linux: Recent news updates: {newsitem.author.get_full_name()} <arch-announce@archlinux.org>', # noqa
                to=['arch-announce@archlinux.org'],
                headers=headers).send()
        return super(NewsCreateView, self).form_valid(form)


class NewsEditView(UpdateView):
    model = News
    form_class = NewsForm
    template_name = "news/add.html"


class NewsDeleteView(DeleteView):
    model = News
    template_name = "news/delete.html"
    success_url = "/news/"


def view_redirect(request, object_id):
    newsitem = get_object_or_404(News, pk=object_id)
    return redirect(newsitem, permanent=True)


@require_POST
def preview(request):
    data = request.POST.get('data', '')
    markup = parse_markdown(data)
    return HttpResponse(markup)

# vim: set ts=4 sw=4 et:
