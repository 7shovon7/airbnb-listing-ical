from datetime import timedelta
import os
import flet as ft
from features.browser_automation import *
from features.firebase_storage import *
import traceback


webdriver_instance = None
is_loop = False
is_initialized = False
operation_completed = False


# Function to load settings from client storage
def load_settings(page):
    settings = page.client_storage.get("settings")
    if settings:
        return settings
    else:
        return {
            "total_months": 6,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "headless": False,
            "credentials_path": None,
            "storage_bucket": "",
            "loop": False,
            "init": True, # to indicate if the app is starting for the first time
        }

# Function to save settings to client storage
def save_settings(page, settings):
    page.client_storage.set("settings", settings)


def main(page: ft.Page):
    global is_loop
    global operation_completed
    settings = load_settings(page)
    is_loop = settings.get('loop', False)
    
    # def choose_file_path(e: ft.FilePickerResultEvent):
    #     if e.files and len(e.files) > 0:
    #         settings["credentials_path"] = e.files[0].path
            
    
    def update_settings(e):
        settings["total_months"] = int(total_months_input.value)
        settings["user_agent"] = user_agent_input.value
        settings["headless"] = headless_checkbox.value
        settings["credentials_path"] = credentials_path.value
        settings["storage_bucket"] = storage_bucket_input.value
        settings["loop"] = loop_checkbox.value
        save_settings(page, settings)
        page.snack_bar.open = True
        page.snack_bar.content = ft.Text("Settings updated!")
        page.update()
        show_main(e)
        
    def choose_credentials_file(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            settings["credentials_path"] = e.files[0].path
            credentials_path.value = settings["credentials_path"]
            credentials_path.update()
    
    
    def shutdown_automation(e):
        global webdriver_instance
        global is_loop
        if webdriver_instance is not None:
            is_loop = False
            webdriver_instance.close_driver()
            webdriver_instance = None
            submit_button.disabled = False
            message_section.value = "Browser closed!"
            page.snack_bar.open = True
            page.snack_bar.content = ft.Text("Automation terminated!")
            page.update()
    
    def submit(e):
        global webdriver_instance
        global is_loop
        global is_initialized
        global operation_completed
        
        # Do not allow operation if the credentials_path and storage_bucket is not set
        if settings.get('credentials_path') is None or settings.get('storage_bucket', '') == '':
            page.snack_bar.open = True
            page.snack_bar.content = ft.Text("Please add Firebase Credentials path and Storage Bucket in settings")
            page.update()
            return
        elif type(url_input.value) == str and 'https://' not in url_input.value:
            page.snack_bar.open = True
            page.snack_bar.content = ft.Text("Need an proper Airbnb listing url starting with 'https://'")
            page.update()
            return
        try:
            submit_button.disabled = True
            message_section.value = "Opening browser..."
            page.update()
            scraper = RootScraper(headless=settings.get('headless', False))
            scraper.open_chromedriver()
            message_section.value = "Checking airbnb website..."
            page.update()
            webdriver_instance = scraper
            airbnb_url = url_input.value
            if not is_initialized:
                initialize_firebase(settings["credentials_path"], settings["storage_bucket"])
                is_initialized = True
            def run_scraper():
                global operation_completed
                scraper.get(airbnb_url)
                ical_content = automate_ical_link_creation(scraper, settings.get("total_months", 6))
                listing_id = airbnb_url.split('/rooms/')[1].split('?')[0].strip()
                message_section.value = "Updating URL..."
                page.update()
                download_url = upload_ical_file(ical_content, listing_id)
                store_ical_link(listing_id, airbnb_url, download_url)
                message_section.value = "URL updated!"
            
                link_field.value = download_url
                
                operation_completed = True
                submit_button.disabled = False
            
                page.snack_bar.open = True
                page.snack_bar.content = ft.Text("Updated!")
            
            if settings.get('loop', False):
                while True and is_loop:
                    run_scraper()
                    sleep_time = random.randint(600, 900)
                    message_section.value = f"The URL will be checked again at {datetime.now() + timedelta(seconds=sleep_time)}"
                    page.update()
                    sleep(sleep_time)
            else:
                run_scraper()
                
            scraper.close_driver()
            webdriver_instance = None
            message_section.value = "Completed!"
        except Exception as ex:
            eror_msg = "Error: " + "".join(traceback.format_exception(None, ex, ex.__traceback__))
            print(eror_msg)
            page.snack_bar.open = True
            page.snack_bar.content = ft.Text(eror_msg)
            message_section.value = "Something went wrong!"
        finally:
            page.update()
            
    def copy_link(e):
        page.set_clipboard(link_field.value)
        # page.clipboard_set_text(link_field.value)
        page.snack_bar.open = True
        page.snack_bar.content = ft.Text("Link copied to clipboard!")
        page.update()
        
    def show_settings(e):
        page.controls.clear()
        page.add(settings_view)
        page.update()

    def show_main(e):
        # global operation_completed
        page.controls.clear()
        page.add(main_view)
        # if operation_completed:
        #     page.add(link_field)
        #     page.add(ft.Row([copy_button], alignment=ft.MainAxisAlignment.CENTER))
        #     page.update()
        page.update()
        
    # Settings Page
    total_months_input = ft.TextField(label="Total number of months to lookup", value=str(settings["total_months"]))
    user_agent_input = ft.TextField(label="Browser User Agent", value=settings["user_agent"])
    headless_checkbox = ft.Checkbox(label="Headless", value=settings["headless"])
    loop_checkbox = ft.Checkbox(label="Loop", value=settings.get("loop", False))
    credentials_picker = ft.FilePicker(on_result=choose_credentials_file)
    credentials_path = ft.Text(value=settings.get('credentials_path', 'No files chosen...'), color=ft.colors.RED if settings.get('credentials_path') is None else None)
    # storage_bucket_input = ft.TextField(label="Storage Bucket", value=settings["storage_bucket"])
    storage_bucket_input = ft.TextField(label="Firebase Storage Bucket", value=settings.get("storage_bucket", "No bucket chosen..."))
    save_button = ft.ElevatedButton(text="Save", icon=ft.icons.SAVE, on_click=update_settings)
    back_button_from_settings = ft.ElevatedButton(text="Back", icon=ft.icons.ARROW_BACK, on_click=show_main)

    settings_view = ft.Column([
        ft.Row(
            [
                back_button_from_settings,
                ft.Text("Settings", size=26, weight=ft.FontWeight.BOLD)
            ],
            # alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        ft.Container(height=6),
        loop_checkbox,
        ft.Container(height=2),
        ft.Text("Credentials File: "),
        ft.Row([
            ft.IconButton(icon=ft.icons.FOLDER_OPEN, on_click=credentials_picker.pick_files),
            credentials_path,
        ]),
        ft.Container(height=2),
        storage_bucket_input,
        ft.Container(height=2),
        total_months_input,
        ft.Container(height=2),
        user_agent_input,
        ft.Container(height=2),
        headless_checkbox,
        ft.Container(height=10),
        ft.Row([save_button], alignment=ft.MainAxisAlignment.CENTER)
    ])

    # Main Page
    url_input = ft.TextField(label="Airbnb Listing URL")
    # listing_id_input = ft.TextField(label="Listing ID")
    submit_button = ft.ElevatedButton(text="Start", icon=ft.icons.ROCKET, on_click=submit)
    shutdown_button = ft.ElevatedButton(text="Close Browser", icon=ft.icons.STOP, color=ft.colors.RED, on_click=shutdown_automation)
    settings_button = ft.ElevatedButton(text="Settings", icon=ft.icons.SETTINGS, on_click=show_settings)
    link_field = ft.TextField(label="Download URL", value="ical url will be here after link generation", read_only=True)
    copy_button = ft.ElevatedButton(text="Copy Link", icon=ft.icons.COPY, on_click=copy_link)
    message_section = ft.Text("")
    page.snack_bar = ft.SnackBar(ft.Text("Submitted!"))

    main_view = ft.Column([
        ft.Row([ft.Text("Airbnb Listing", size=26, weight=ft.FontWeight.BOLD), settings_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(height=6),
        url_input,
        ft.Container(),
        ft.Row([submit_button, shutdown_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(),
        link_field,
        ft.Row([copy_button], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=16),
        ft.Row([message_section], alignment=ft.MainAxisAlignment.CENTER),
    ])

    # Show Main Page initially
    page.overlay.append(credentials_picker)
    page.add(main_view)


ft.app(main)
