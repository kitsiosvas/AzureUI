from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock

class PopupManager:
    def __init__(self, title, message, progress_interval=0.5):
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=20)
        self.progress_bar.value = 0
        self.progress_interval = progress_interval
        self.progress_schedule = None
        self.popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        self.popup.open()
        if self.progress_schedule:
            self.progress_schedule.cancel()
        self.progress_schedule = Clock.schedule_interval(self.update_progress, self.progress_interval)

    def update_progress(self, dt):
        """Update the progress bar value."""
        self.progress_bar.value = (self.progress_bar.value + 10) % 100

    def dismiss(self):
        if self.progress_schedule:
            self.progress_schedule.cancel()
        self.popup.dismiss()