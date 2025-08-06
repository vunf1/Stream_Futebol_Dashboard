import customtkinter as ctk
from multiprocessing import Queue

from helpers.notification.toast import display_notification


def server_main(notification_queue: Queue):
    """
    Run on its own process. Listens on notification_queue
    and displays toasts in a single CTk loop, better for stacking nicely with multiple instance.
    """
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.withdraw()

    def poll_queue():
        while not notification_queue.empty():
            title, message, opts = notification_queue.get()
            display_notification(title, message, **opts)
        root.after(100, poll_queue)

    poll_queue()
    root.mainloop()


if __name__ == '__main__':
    from multiprocessing import Manager
    mgr = Manager()
    q = mgr.Queue()
    server_main(q) # type: ignore
