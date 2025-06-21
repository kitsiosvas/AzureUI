from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from kivy.event import EventDispatcher

class DataTableHeader(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(30)
        self.color = (1, 1, 1, 1)
        with self.canvas.before:
            Color(0.1, 0.2, 0.6, 1)
            self.rect = Rectangle()
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class DataTableCell(ButtonBehavior, Label):
    def __init__(self, row_index, **kwargs):
        super().__init__(**kwargs)
        self.row_index = row_index
        self.size_hint_y = None
        self.height = dp(30)
        self.color = (0, 0, 0, 1)
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            self.rect = Rectangle()
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        self.parent.table.select_row(self.row_index)

class DataTableRow(BoxLayout):
    selected = BooleanProperty(False)
    table = ObjectProperty(None)

    def __init__(self, row_data, widths, bg_color, table, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(30), **kwargs)
        self.bg_color_default = bg_color
        self.table = table
        self.cells = []
        for i, cell_data in enumerate(row_data):
            cell = DataTableCell(
                row_index=len(table.rows),
                text=str(cell_data),
                size_hint_x=None,
                width=widths[i]
            )
            self.add_widget(cell)
            self.cells.append(cell)
        self.update_colors()

    def update_colors(self):
        color = [0.5, 0.7, 0.9, 1] if self.selected else self.bg_color_default
        for cell in self.cells:
            cell.bg_color.rgba = color

class CustomDataTable(BoxLayout, EventDispatcher):
    __events__ = ('on_row_select',)

    def __init__(self, column_data, row_data, column_widths=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        EventDispatcher.__init__(self)
        self.column_data = column_data
        self.row_data = row_data
        self.column_widths = column_widths or [dp(100)] * len(column_data)
        self.rows = []
        self.selected_row_index = None

        # Header layout
        self.header_layout = GridLayout(cols=len(column_data), size_hint=(None, None), height=dp(30))
        self.header_layout.bind(minimum_width=self.header_layout.setter("width"))
        for i, col_title in enumerate(column_data):
            header = DataTableHeader(text=col_title, size_hint_x=None, width=self.column_widths[i])
            self.header_layout.add_widget(header)
        self.add_widget(self.header_layout)

        # Scrollable content
        self.scroll_view = ScrollView(
            do_scroll_x=True,
            do_scroll_y=True,
            scroll_type=['bars', 'content'],  # Enable drag and scrollbars
            bar_width=dp(10),  # Visible scrollbars
            bar_color=[0.7, 0.7, 0.7, 1],  # Gray bars
            bar_inactive_color=[0.3, 0.3, 0.3, 1]
        )
        self.row_container = BoxLayout(orientation='vertical', size_hint=(None, None))
        self.row_container.bind(minimum_height=self.row_container.setter('height'))
        self.row_container.bind(minimum_width=self.setter('minimum_width'))
        self.update_row_data(row_data)

        self.scroll_view.add_widget(self.row_container)
        self.add_widget(self.scroll_view)

        # Bind scroll_x for header alignment and debug
        self.scroll_view.bind(scroll_x=self.update_header_position)

    def update_header_position(self, instance, value):
        """Keep header aligned with rows."""
        self.header_layout.pos[0] = self.scroll_view.width * value - value * self.row_container.width

    def update_row_data(self, row_data):
        """Update table with new row data."""
        self.row_container.clear_widgets()
        self.rows = []
        self.selected_row_index = None
        self.row_data = row_data
        total_width = sum([w.value if hasattr(w, 'value') else w for w in self.column_widths])
        self.row_container.width = total_width
        self.header_layout.width = total_width
        for i, row in enumerate(row_data):
            bg_color = [0.95, 0.95, 0.95, 1] if i % 2 == 0 else [0.85, 0.85, 0.85, 1]
            row_widget = DataTableRow(row, self.column_widths, bg_color, table=self)
            self.row_container.add_widget(row_widget)
            self.rows.append(row_widget)

    def select_row(self, row_index):
        """Select a row and dispatch on_row_select event."""
        if row_index < 0 or row_index >= len(self.rows):
            return
        self.selected_row_index = row_index
        for i, row in enumerate(self.rows):
            row.selected = (i == row_index)
            row.update_colors()
        if row_index < len(self.row_data):
            self.dispatch('on_row_select', self.row_data[row_index][0])

    def on_row_select(self, value):
        """Default handler for row selection."""
        pass
