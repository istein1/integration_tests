# -*- coding: utf-8 -*-
""" A model of Workloads page in CFME
"""
from navmazing import NavigateToAttribute
from widgetastic.widget import Text, View
from widgetastic_patternfly import Button, Dropdown

from cfme.base.login import BaseLoggedInPage
from cfme.utils.appliance import NavigatableMixin
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep
from widgetastic_manageiq import Accordion, ManageIQTree, Search, ItemsToolBarViewSelector


class WorkloadsToolbar(View):
    """Toolbar on the workloads page"""
    history = Dropdown(title='History')
    reload = Button(title='Reload current display')
    configuration = Dropdown('Configuration')
    policy = Dropdown('Policy')
    lifecycle = Dropdown('Lifecycle')
    download = Dropdown(title='Download')
    view_selector = View.nested(ItemsToolBarViewSelector)


class WorkloadsView(BaseLoggedInPage):
    search = View.nested(Search)
    toolbar = View.nested(WorkloadsToolbar)

    @property
    def in_workloads(self):
        return (self.logged_in_as_current_user and
                self.navigation.currently_selected == ['Services', 'Workloads'])

    @View.nested
    class vms(Accordion):  # noqa
        ACCORDION_NAME = "VMs & Instances"
        tree = ManageIQTree()

        def select_global_filter(self, filter_name):
            self.tree.click_path("All VMs & Instances", "Global Filters", filter_name)

        def select_my_filter(self, filter_name):
            self.tree.click_path("All VMs & Instances", "My Filters", filter_name)

        def clear_filter(self):
            self.parent.search.clear_simple_search()
            self.tree.click_path("All VMs & Instances")

    @View.nested
    class templates(Accordion):  # noqa
        ACCORDION_NAME = "Templates & Images"
        tree = ManageIQTree()

        def select_global_filter(self, filter_name):
            self.tree.click_path("All Templates & Images", "Global Filters", filter_name)

        def select_my_filter(self, filter_name):
            self.tree.click_path("All Templates & Images", "My Filters", filter_name)

        def clear_filter(self):
            self.parent.search.clear_simple_search()
            self.tree.click_path("All Templates & Images")

    @View.nested
    class toolbar(View):  # noqa
        """
         represents workloads toolbar and its controls
        """
        configuration = Dropdown(text='Configuration')
        policy = Dropdown(text='Policy')
        lifecycle = Dropdown(text='Lifecycle')
        download = Dropdown(text='Download')
        view_selector = View.nested(ItemsToolBarViewSelector)


class WorkloadsDefaultView(WorkloadsView):
    title = Text("#explorer_title_text")

    @property
    def is_displayed(self):
        return (
            self.in_workloads and
            self.title.text == 'All VMs & Instances' and
            self.vms.is_opened)


class WorkloadsVM(WorkloadsDefaultView):

    @property
    def is_displayed(self):
        return (
            self.in_workloads and
            self.title.text == 'All VMs & Instances' and
            self.vms.is_opened and
            self.vms.tree.currently_selected == [
                "All VMs & Instances"])


class WorkloadsTemplate(WorkloadsDefaultView):

    @property
    def is_displayed(self):
        return (
            self.in_workloads and
            self.title.text == 'All Templates & Images' and
            self.templates.is_opened and
            self.templates.tree.currently_selected == [
                "All Templates & Images"])


class BaseWorkloads(NavigatableMixin):
    def __init__(self, appliance):
        self.appliance = appliance


class VmsInstances(BaseWorkloads):
    """
        This is fake class mainly needed for navmazing navigation

    """
    pass


class TemplatesImages(BaseWorkloads):
    """
        This is fake class mainly needed for navmazing navigation

    """
    pass


@navigator.register(VmsInstances, 'All')
class AllVMs(CFMENavigateStep):
    VIEW = WorkloadsVM
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self, *args, **kwargs):
        self.prerequisite_view.navigation.select('Services', 'Workloads')
        self.view.search.clear_simple_search()
        self.view.vms.clear_filter()


@navigator.register(TemplatesImages, 'All')
class AllTemplates(CFMENavigateStep):
    VIEW = WorkloadsTemplate
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self, *args, **kwargs):
        self.prerequisite_view.navigation.select('Services', 'Workloads')
        self.view.search.clear_simple_search()
        self.view.templates.clear_filter()
