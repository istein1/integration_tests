import attr

from navmazing import NavigateToAttribute, NavigateToSibling
from widgetastic.utils import Fillable
from widgetastic.exceptions import NoSuchElementException

from cfme.base.ui import Server

from cfme.utils import version
from cfme.common.provider import BaseProvider, provider_types
from cfme.common.provider_views import (PhysicalProviderAddView,
                                        PhysicalProvidersView,
                                        PhysicalProviderDetailsView,
                                        PhysicalProviderEditView)
from cfme.modeling.base import BaseCollection
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep
from cfme.utils.pretty import Pretty
from cfme.utils.varmeth import variable
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils.log import logger
from cfme.utils.net import resolve_hostname


@attr.s(hash=False)
class PhysicalProvider(Pretty, BaseProvider, Fillable):
    """
    Abstract model of an infrastructure provider in cfme. See VMwareProvider or RHEVMProvider.
    """
    provider_types = {}
    category = "physical"
    pretty_attrs = ['name']
    STATS_TO_MATCH = ['num_server']
    string_name = "Physical Infrastructure"
    page_name = "infrastructure"
    db_types = ["PhysicalInfraManager"]

    name = attr.ib(default=None)
    key = attr.ib(default=None)

    def __attrs_post_init__(self):
        super(PhysicalProvider, self).__attrs_post_init__()
        self.parent = self.appliance.collections.physical_providers

    @property
    def hostname(self):
        return getattr(self.default_endpoint, "hostname", None)

    @property
    def ip_address(self):
        return getattr(self.default_endpoint, "ipaddress", resolve_hostname(str(self.hostname)))

    @variable(alias='ui')
    def num_server(self):
        view = navigate_to(self, 'Details')
        try:
            num = view.entities.summary('Relationships').get_text_of('Physical Servers')
        except NoSuchElementException:
            logger.error("Couldn't find number of servers")
        return int(num)

    def delete(self, cancel=True):
        """
        Deletes a provider from CFME

        Args:
            cancel: Whether to cancel the deletion, defaults to True
        """
        view = navigate_to(self, 'Details')
        item_title = version.pick({'5.9': 'Remove this {} Provider from Inventory',
                                   version.LOWEST: 'Remove this {} Provider'})
        view.toolbar.configuration.item_select(item_title.format("Infrastructure"),
                                               handle_alert=not cancel)
        if not cancel:
            view.flash.assert_no_error()


@attr.s
class PhysicalProviderCollection(BaseCollection):
    """Collection object for PhysicalProvider object
    """

    ENTITY = PhysicalProvider

    def all(self):
        view = navigate_to(self, 'All')
        provs = view.entities.get_all(surf_pages=True)

        # trying to figure out provider type and class
        # todo: move to all providers collection later
        def _get_class(pid):
            prov_type = self.appliance.rest_api.collections.providers.get(id=pid)['type']
            for prov_class in provider_types('infra').values():
                if prov_class.db_types[0] in prov_type:
                    return prov_class

        return [self.instantiate(prov_class=_get_class(p.data['id']), name=p.name) for p in provs]

    def instantiate(self, prov_class, *args, **kwargs):
        return prov_class.from_collection(self, *args, **kwargs)

    def create(self, prov_class, *args, **kwargs):
        # ugly workaround until I move everything to main class
        class_attrs = [at.name for at in attr.fields(prov_class)]
        init_kwargs = {}
        create_kwargs = {}
        for name, value in kwargs.items():
            if name not in class_attrs:
                create_kwargs[name] = value
            else:
                init_kwargs[name] = value

        obj = self.instantiate(prov_class, *args, **init_kwargs)
        obj.create(**create_kwargs)
        return obj


@navigator.register(PhysicalProviderCollection, 'All')
@navigator.register(Server, 'PhysicalProviders')
@navigator.register(PhysicalProvider, 'All')
class All(CFMENavigateStep):
    # This view will need to be created
    VIEW = PhysicalProvidersView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Physical Infrastructure', 'Providers')

    def resetter(self):
        # Reset view and selection
        pass


@navigator.register(PhysicalProvider, 'Details')
class Details(CFMENavigateStep):
    VIEW = PhysicalProviderDetailsView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.entities.get_entity(name=self.obj.name, surf_pages=True).click()


@navigator.register(PhysicalProvider, 'Edit')
class Edit(CFMENavigateStep):
    VIEW = PhysicalProviderEditView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select(
            'Edit this Infrastructure Provider')


@navigator.register(PhysicalProviderCollection, 'Add')
@navigator.register(PhysicalProvider, 'Add')
class Add(CFMENavigateStep):
    VIEW = PhysicalProviderAddView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select(
            'Add a New Physical Provider'
        )
