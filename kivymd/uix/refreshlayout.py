"""
Components/RefreshLayout
========================

Example
-------

.. code-block:: python

    from kivymd.app import MDApp
    from kivy.clock import Clock
    from kivy.lang import Builder
    from kivy.factory import Factory
    from kivy.properties import StringProperty

    from kivymd.uix.button import MDIconButton
    from kivymd.icon_definitions import md_icons
    from kivymd.uix.list import ILeftBodyTouch, OneLineIconListItem
    from kivymd.theming import ThemeManager
    from kivymd.utils import asynckivy

    Builder.load_string('''
    <ItemForList>
        text: root.text

        IconLeftSampleWidget:
            icon: root.icon


    <Example@FloatLayout>

        MDBoxLayout:
            orientation: 'vertical'

            MDToolbar:
                title: app.title
                md_bg_color: app.theme_cls.primary_color
                background_palette: 'Primary'
                elevation: 10
                left_action_items: [['menu', lambda x: x]]

            MDScrollViewRefreshLayout:
                id: refresh_layout
                refresh_callback: app.refresh_callback
                root_layout: root

                MDGridLayout:
                    id: box
                    adaptive_height: True
                    cols: 1
    ''')


    class IconLeftSampleWidget(ILeftBodyTouch, MDIconButton):
        pass


    class ItemForList(OneLineIconListItem):
        icon = StringProperty()


    class Example(MDApp):
        title = 'Example Refresh Layout'
        screen = None
        x = 0
        y = 15

        def build(self):
            self.screen = Factory.Example()
            self.set_list()

            return self.screen

        def set_list(self):
            async def set_list():
                names_icons_list = list(md_icons.keys())[self.x:self.y]
                for name_icon in names_icons_list:
                    await asynckivy.sleep(0)
                    self.screen.ids.box.add_widget(
                        ItemForList(icon=name_icon, text=name_icon))
            asynckivy.start(set_list())

        def refresh_callback(self, *args):
            '''A method that updates the state of your application
            while the spinner remains on the screen.'''

            def refresh_callback(interval):
                self.screen.ids.box.clear_widgets()
                if self.x == 0:
                    self.x, self.y = 15, 30
                else:
                    self.x, self.y = 0, 15
                self.set_list()
                self.screen.ids.refresh_layout.refresh_done()
                self.tick = 0

            Clock.schedule_once(refresh_callback, 1)


    Example().run()
"""

from typing import NoReturn, Union

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ColorProperty, NumericProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView

from kivymd.theming import ThemableBehavior

Builder.load_string(
    """
#:import Window kivy.core.window.Window


<RefreshSpinner>

    AnchorLayout:
        id: body_spinner
        size_hint: None, None
        size: dp(46), dp(46)
        y: Window.height
        pos_hint: {'center_x': .5}
        anchor_x: 'center'
        anchor_y: 'center'

        canvas:
            Clear
            Color:
                rgba: root.theme_cls.primary_dark
            Ellipse:
                pos: self.pos
                size: self.size

        MDSpinner:
            id: spinner
            size_hint: None, None
            size: dp(30), dp(30)
            color: 1, 1, 1, 1
"""
)


class _RefreshScrollEffect(DampedScrollEffect):
    """
    This class is simply based on DampedScrollEffect.
    If you need any documentation please look at
    :class:`~kivy.effects.dampedscrolleffect`.
    """

    min_scroll_to_reload = NumericProperty("-100dp")
    """
    Minimum overscroll value to reload.

    :attr:`min_scroll_to_reload` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `'-100dp'`.
    """

    def on_overscroll(
        self, instance_refresh_scroll_effect, overscroll: Union[int, float]
    ) -> bool:
        if overscroll < self.min_scroll_to_reload:
            scroll_view = self.target_widget.parent
            scroll_view._did_overscroll = True
            return True
        else:
            return False


class MDScrollViewRefreshLayout(ScrollView):
    root_layout = ObjectProperty()
    """
    The spinner will be attached to this layout.

    :attr:`root_layout` is a :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self.effect_cls = _RefreshScrollEffect
        self._work_spinnrer = False
        self._did_overscroll = False
        self.refresh_spinner = None

    def on_touch_up(self, *args):
        if self._did_overscroll and not self._work_spinnrer:
            if self.refresh_callback:
                self.refresh_callback()
            if not self.refresh_spinner:
                self.refresh_spinner = RefreshSpinner(_refresh_layout=self)
                self.root_layout.add_widget(self.refresh_spinner)
            self.refresh_spinner.start_anim_spinner()
            self._work_spinnrer = True
            self._did_overscroll = False
            return True

        return super().on_touch_up(*args)

    def refresh_done(self) -> NoReturn:
        if self.refresh_spinner:
            self.refresh_spinner.hide_anim_spinner()


class RefreshSpinner(ThemableBehavior, FloatLayout):
    spinner_color = ColorProperty([1, 1, 1, 1])
    """
    Color of spinner.

    :attr:`spinner_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `[1, 1, 1, 1]`.
    """

    # kivymd.refreshlayout.MDScrollViewRefreshLayout object
    _refresh_layout = ObjectProperty()

    def start_anim_spinner(self) -> NoReturn:
        spinner = self.ids.body_spinner
        Animation(
            y=spinner.y - self.theme_cls.standard_increment * 2 + dp(10),
            d=0.8,
            t="out_elastic",
        ).start(spinner)

    def hide_anim_spinner(self) -> NoReturn:
        spinner = self.ids.body_spinner
        anim = Animation(y=Window.height, d=0.8, t="out_elastic")
        anim.bind(on_complete=self.set_spinner)
        anim.start(spinner)

    def set_spinner(self, *args) -> NoReturn:
        body_spinner = self.ids.body_spinner
        body_spinner.size = (dp(46), dp(46))
        body_spinner.y = Window.height
        body_spinner.opacity = 1
        spinner = self.ids.spinner
        spinner.size = (dp(30), dp(30))
        spinner.opacity = 1
        self._refresh_layout._work_spinnrer = False
        self._refresh_layout._did_overscroll = False
