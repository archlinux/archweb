from django.core import mail
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User


from news.models import News


class NewTest(TestCase):

    def test_feed(self):
        response = self.client.get('/feeds/news/')
        self.assertEqual(response.status_code, 200)

    def test_sitemap(self):
        response = self.client.get('/sitemap-news.xml')
        self.assertEqual(response.status_code, 200)

    def test_newsitem(self):
        response = self.client.get('/news/404', follow=True)
        self.assertEqual(response.status_code, 404)


class NewsCrud(TransactionTestCase):
    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser('admin',
                                                  'admin@archlinux.org',
                                                  password)
        self.client.post('/login/', {
                                    'username': self.user.username,
                                    'password': password
        })

    def tearDown(self):
        News.objects.all().delete()
        self.user.delete()

    def create(self, title='Bash broken', content='Broken in [testing]', announce=False):
        data = {
            'title': title,
            'content': content,
        }
        if announce:
            data['send_announce'] = 'on'
        return self.client.post('/news/add/', data, follow=True)

    def testCreateItem(self):
        title = 'Bash broken'
        response = self.create(title)
        self.assertEqual(response.status_code, 200)

        news = News.objects.first()
        self.assertEqual(news.author, self.user)
        self.assertEqual(news.title, title)

    def testView(self):
        self.create()
        news = News.objects.first()

        response = self.client.get(news.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def testRedirectId(self):
        self.create()
        news = News.objects.first()

        response = self.client.get('/news/{}'.format(news.id), follow=True)
        self.assertEqual(response.status_code, 200)

    def testSendAnnounce(self):
        title = 'New glibc'
        self.create(title, announce=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(title, mail.outbox[0].subject)

    def testPreview(self):
        response = self.client.post('/news/preview/', {'data': '**body**'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('<p><strong>body</strong></p>', response.content.decode())
