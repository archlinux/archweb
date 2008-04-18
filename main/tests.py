## test cases
from django.test import TestCase
from main.models import Mirror, Press, AltForum, Donor, News
from main.models import Arch, Repo, Package, PackageFile, PackageDepend
from main.models import Todolist, TodolistPkg, Wikipage
from django.contrib.auth.models import User

class ModelTest(TestCase):
    fixtures = ['arches.json', 'repos.json', 'test_packages.json']

    def setUp(self):
        self.user = User(id=1,username='tester',first_name='test', 
                         last_name='user', password='testuser',
                         is_active=True, is_staff=True)
        self.user.save()
        self.orphan = User(id=0,first_name='Orphans')
        pass

    def testPackageGetDepends(self):
        """
        Test the Package object's get_depends() method
        """
        p = Package.objects.get(pkgname='abs',arch__name__iexact='i686')
        expected = [(7L, 'bash', ''), (None, 'rsync', None)]
        results = p.get_depends()
        self.failUnlessEqual(results, expected)
        del p
    
    def testPackageGetRequiredBy(self):
        """
        Test the Package object's get_requiredby() method
        """
        p = Package.objects.get(pkgname='iproute',arch__name__iexact='i686')
        expected = [Package.objects.get(id=123),Package.objects.get(id=163)]
        results = p.get_requiredby()
        self.failUnlessEqual(results, expected)
        del p

    def testGetFlagStats(self):
        """
        Test the PackageManager get_flag_stats method
        """
        results = Package.objects.get_flag_stats()
        expected = [(self.orphan, 0L, 0L),(self.user, 346L, 0L)]
        self.failUnlessEqual(results, expected)
        del results


