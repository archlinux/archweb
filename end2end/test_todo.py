from . import BaseTestCase


class TodoTestCase(BaseTestCase):

    def data(self):
        name = 'glibc rebuild'
        pkgs = ['pacman', 'linux']
        desc = 'The glibc 8 rebuild, read the ABI changes'
        return name, desc, pkgs

    def create_todolist(self, name, desc, pkgs):
        self.get('/todo/add')
        id_name = self.selenium.find_element_by_id("id_name")
        id_name.send_keys(name)
        description = self.selenium.find_element_by_id("id_description")
        description.send_keys(desc)
        packages = self.selenium.find_element_by_id("id_raw")
        packages.send_keys('\n'.join(pkgs))
        self.submit()

    def test_create(self):
        name, desc, pkgs = self.data()
        self.create_todolist(name, desc, pkgs)

        self.assertIn('Todo List: {}'.format(name), self.selenium.page_source)
        for pkg in pkgs:
            self.assertIn(pkg, self.selenium.page_source)

    def test_delete(self):
        name, desc, pkgs = self.data()

        self.create_todolist(name, desc, pkgs)
        self.selenium.find_element_by_link_text('Delete Todo List').click()
        self.assertIn('Delete Todo List: {}'.format(name), self.selenium.page_source)

        self.submit()
        self.assertNotIn('Todo List: {}'.format(name), self.selenium.page_source)

    def test_edit(self):
        name, desc, pkgs = self.data()
        newpkgs = pkgs[:]
        newpkgs.append('nonexistant')

        self.create_todolist(name, desc, newpkgs)
        self.selenium.find_element_by_link_text('Edit Todo List').click()
        packages = self.selenium.find_element_by_id("id_raw")
        packages.send_keys('\n'.join(pkgs))
        self.submit()

        self.assertIn('Todo List: {}'.format(name), self.selenium.page_source)
        for pkg in pkgs:
            self.assertIn(pkg, self.selenium.page_source)
        self.assertNotIn('nonexistant', self.selenium.page_source)

    def test_complete(self):
        name, desc, pkgs = self.data()

        self.create_todolist(name, desc, pkgs)
        for elem in self.selenium.find_elements_by_partial_link_text('Incomplete'):
            elem.click()

        self.get('/todo/{}'.format(name))
        elems = self.selenium.find_elements_by_partial_link_text('Incomplete')
        self.assertFalse(elems)

        self.get('/todo/')
        self.assertTrue(self.selenium.find_element_by_class_name('complete'))

        # Reverse again
        for elem in self.selenium.find_elements_by_partial_link_text('Ccomplete'):
            elem.click()

        self.get('/todo/{}'.format(name))
        elems = self.selenium.find_elements_by_partial_link_text('Complete')
        self.assertFalse(elems)

    def test_filter_repo(self):
        name, desc, pkgs = self.data()

        self.create_todolist(name, desc, pkgs)

        # Deselect [core] repo
        self.selenium.find_element_by_id('id_repo_core').click()
        for elem in self.selenium.find_elements_by_partial_link_text('Incomplete'):
            self.assertFalse(elem.is_displayed())

    def test_filter_incomplete(self):
        name, desc, pkgs = self.data()

        self.create_todolist(name, desc, pkgs)

        # Flag one complete
        self.selenium.find_element_by_partial_link_text('Incomplete').click()

        # Filter on incomplete
        self.selenium.find_element_by_id('id_incomplete').click()

        for elem in self.selenium.find_elements_by_partial_link_text('Complete'):
            self.assertFalse(elem.is_displayed())

    def test_view_pkg(self):
        name, desc, pkgs = self.data()

        self.create_todolist(name, desc, pkgs)
        for pkg in pkgs:
            self.selenium.find_element_by_link_text(pkg).click()
            self.assertIn(pkg, self.selenium.title)
            self.assertIn('/packages/', self.selenium.current_url)
            self.selenium.back()
