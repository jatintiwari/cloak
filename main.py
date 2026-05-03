import sys
import os
import threading
import traceback
import objc

# OS Check
if sys.platform != "darwin":
    sys.exit(1)

try:
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSView, NSPanel, NSScreen,
        NSWindowStyleMaskBorderless, NSWindowStyleMaskResizable,
        NSBackingStoreBuffered, NSNormalWindowLevel, NSColor, NSMakeRect,
        NSVisualEffectView, NSVisualEffectMaterialUnderWindowBackground,
        NSVisualEffectBlendingModeBehindWindow,
        NSWindowCollectionBehaviorCanJoinAllSpaces,
        NSWindowCollectionBehaviorIgnoresCycle,
        NSApplicationActivationPolicyAccessory,
        NSMenu, NSMenuItem,
        NSWindowSharingNone,
        NSStatusBar, NSVariableStatusItemLength,
        NSImage, NSBezierPath, NSAlert, NSEvent
    )
    from WebKit import WKWebView, WKWebViewConfiguration
    from Foundation import NSURL, NSURLRequest, NSObject, NSSize
    from PyObjCTools import AppHelper
except ImportError:
    sys.exit(1)

# Helper to check for Accessibility Permissions
def check_accessibility():
    # Load ApplicationServices to check if the app is trusted for hotkeys
    # We need to properly load the functions from the bundle
    bundle_path = '/System/Library/Frameworks/ApplicationServices.framework'
    if not os.path.exists(bundle_path):
        return

    objc.loadBundle('ApplicationServices', globals(), bundle_path=bundle_path)
    
    # Try to use the function if it's available in the loaded bundle
    # AXIsProcessTrusted is a common C function for this
    is_trusted = False
    try:
        # Check if the function was exported to globals by loadBundle
        if 'AXIsProcessTrusted' in globals():
            is_trusted = AXIsProcessTrusted()
        else:
            # Fallback: if not in globals, it might need to be specifically loaded
            # but usually pyobjc handles this for common frameworks if they are loaded.
            # As a safeguard, assume trusted if we can't check, to avoid blocking.
            is_trusted = True
    except Exception:
        is_trusted = True

    if not is_trusted:
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Accessibility Permission Required")
        alert.setInformativeText_("Cloak needs Accessibility permission for the global hotkey to work.\n\nPlease grant it in System Settings > Privacy & Security > Accessibility.")
        alert.addButtonWithTitle_("OK")
        alert.runModal()

# Custom Panel subclass to ensure it can receive keyboard input
class KeyPanel(NSPanel):
    def canBecomeKeyWindow(self):
        return True
    def canBecomeMainWindow(self):
        return True

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        try:
            self.app_instance.setup_ui()
            self.app_instance.setup_menu()
            self.app_instance.setup_status_bar()
            self.app_instance.setup_hotkeys()
            AppHelper.callAfter(check_accessibility)
            # Show the window on the next run-loop tick (after the status bar
            # icon has been drawn and the event loop is fully running).
            AppHelper.callAfter(self.app_instance._do_show)
        except Exception:
            pass

    def applicationShouldHandleReopen_hasVisibleWindows_(self, sender, flag):
        try:
            # If the app is already running and the icon is clicked in Finder
            self.app_instance._do_show()
            return True
        except Exception:
            return True

class CloakApp:
    def __init__(self, url="https://gemini.google.com"):
        self.url = url
        self.window = None
        self.is_visible = False
        self.ns_app = None
        self.listener = None
        
    def _do_show(self):
        if not self.window: return
        # activateIgnoringOtherApps_ gives the process focus, then
        # orderFrontRegardless forces the window to the front unconditionally.
        # No policy switching needed or wanted — it breaks foreground behaviour.
        self.ns_app.activateIgnoringOtherApps_(True)
        self.window.orderFrontRegardless()
        self.window.makeKeyAndOrderFront_(None)
        self.window.makeFirstResponder_(self.webview)
        self.is_visible = True

    def setup_hotkeys(self):
        try:
            # Cmd is 1 << 20, Option is 1 << 19, KeyDown is 1 << 10
            CMD_MASK = 1 << 20
            OPT_MASK = 1 << 19
            KEYDOWN_MASK = 1 << 10

            def handle_global_event(event):
                flags = event.modifierFlags()
                if (flags & CMD_MASK) and (flags & OPT_MASK):
                    chars = event.charactersIgnoringModifiers()
                    if chars and chars.lower() == 'o':
                        AppHelper.callAfter(self._do_toggle)

            def handle_local_event(event):
                flags = event.modifierFlags()
                if (flags & CMD_MASK) and (flags & OPT_MASK):
                    chars = event.charactersIgnoringModifiers()
                    if chars and chars.lower() == 'o':
                        AppHelper.callAfter(self._do_toggle)
                        return None # Consume the event so it doesn't beep or type
                return event

            # Global monitor listens when the app is in the background
            self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                KEYDOWN_MASK, handle_global_event
            )
            
            # Local monitor listens when the app is in the foreground
            self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                KEYDOWN_MASK, handle_local_event
            )
        except Exception:
            pass

    def setup_status_bar(self):
        self.status_bar = NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(NSVariableStatusItemLength)
        self.status_button = self.status_item.button()
        
        # Set target and action for the button.
        # IMPORTANT: Do NOT call self.status_item.setMenu_() — attaching a menu
        # to the status item intercepts ALL clicks (left and right) and prevents
        # the action/target from ever being called. Instead we handle right-click
        # manually inside statusToggle_.
        self.status_button.setTarget_(self)
        self.status_button.setAction_("statusToggle:")
        # Receive both left-click (1) and right-click (2) events
        self.status_button.sendActionOn_(1 | 2)
        
        image_path = os.path.join(os.path.dirname(__file__), "cloak.png")
        if not os.path.exists(image_path):
            image_path = os.path.join(os.environ.get('RESOURCEPATH', ''), "cloak.png")

        if os.path.exists(image_path):
            original_image = NSImage.alloc().initByReferencingFile_(image_path)
            
            # Create a rounded version of the icon
            size = NSSize(18, 18)
            rounded_image = NSImage.alloc().initWithSize_(size)
            rounded_image.lockFocus()
            
            # Clip to a circle
            path = NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(0, 0, size.width, size.height))
            path.addClip()
            
            original_image.drawInRect_(NSMakeRect(0, 0, size.width, size.height))
            rounded_image.unlockFocus()
            
            rounded_image.setTemplate_(True)
            self.status_button.setImage_(rounded_image)
        else:
            self.status_button.setTitle_("⦿")
        
        # Build the context menu (shown on right-click only)
        self.status_menu = NSMenu.alloc().init()
        toggle_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show/Hide Window", "statusToggle:", ""
        )
        toggle_item.setTarget_(self)
        self.status_menu.addItem_(toggle_item)
        self.status_menu.addItem_(NSMenuItem.separatorItem())
        
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", "q"
        )
        self.status_menu.addItem_(quit_item)
        # NOTE: intentionally NOT calling self.status_item.setMenu_(self.status_menu)
        # so that left-click still fires statusToggle_

    def statusToggle_(self, sender):
        # Detect right-click / ctrl-click → show context menu instead of toggling
        event = NSApp().currentEvent()
        if event is not None:
            CTRL_CLICK = (1 << 18)  # NSControlKeyMask
            flags = event.modifierFlags()
            etype = event.type()
            # type 3 = NSEventTypeRightMouseDown
            if etype == 3 or (flags & CTRL_CLICK):
                self.status_item.popUpStatusItemMenu_(self.status_menu)
                return
        # We are already on the main thread — call directly, no callAfter needed.
        # Using callAfter here introduced a race: the toggle ran one run-loop tick
        # later when the current event was already gone, causing missed activations.
        self._do_toggle()

    def setup_menu(self):
        main_menu = NSMenu.alloc().init()
        app_menu_item = NSMenuItem.alloc().init()
        main_menu.addItem_(app_menu_item)
        app_menu = NSMenu.alloc().init()
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Cloak", "terminate:", "q"
        )
        app_menu.addItem_(quit_item)
        app_menu_item.setSubmenu_(app_menu)
        NSApp().setMainMenu_(main_menu)

    def setup_ui(self):
        self.ns_app = NSApplication.sharedApplication()
        self.ns_app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        
        style_mask = NSWindowStyleMaskBorderless | NSWindowStyleMaskResizable
        screen = NSScreen.mainScreen()
        if not screen: return
            
        screen_rect = screen.frame()
        width, height = 1000, 700
        x = (screen_rect.size.width - width) / 2
        y = (screen_rect.size.height - height) / 2
        rect = NSMakeRect(x, y, width, height)
        
        self.window = KeyPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style_mask, NSBackingStoreBuffered, False
        )
        
        self.window.setSharingType_(NSWindowSharingNone)
        self.window.setLevel_(NSNormalWindowLevel)
        self.window.setCollectionBehavior_(
            # CanJoinAllSpaces  — window follows you across Spaces
            # IgnoresCycle     — hidden from Cmd+Tab / Expose cycling
            # NOTE: do NOT include NSWindowCollectionBehaviorStationary here.
            # That flag tells the window server the window is decorative and
            # should not be raised/ordered, which is why repeated clicks were
            # needed before the window would appear.
            NSWindowCollectionBehaviorCanJoinAllSpaces |
            NSWindowCollectionBehaviorIgnoresCycle
        )
        
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setBecomesKeyOnlyIfNeeded_(False)
        
        content_view = self.window.contentView()
        visual_effect_view = NSVisualEffectView.alloc().initWithFrame_(content_view.bounds())
        visual_effect_view.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
        visual_effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        visual_effect_view.setState_(1)
        visual_effect_view.setAutoresizingMask_(2 | 16)
        visual_effect_view.setWantsLayer_(True)
        visual_effect_view.layer().setCornerRadius_(16.0)
        visual_effect_view.layer().setMasksToBounds_(True)
        content_view.addSubview_(visual_effect_view)
        
        config = WKWebViewConfiguration.alloc().init()
        config.setMediaTypesRequiringUserActionForPlayback_(0xFFFFFFFF)
        
        self.webview = WKWebView.alloc().initWithFrame_configuration_(
            content_view.bounds(), config
        )
        
        if hasattr(self.webview, 'setAudioMuted_'):
            self.webview.setAudioMuted_(True)
            
        self.webview.setAutoresizingMask_(2 | 16)
        self.webview.setOpaque_(False)
        self.webview.setBackgroundColor_(NSColor.clearColor())
        content_view.addSubview_(self.webview)
        
        url_obj = NSURL.URLWithString_(self.url)
        request = NSURLRequest.requestWithURL_(url_obj)
        self.webview.loadRequest_(request)
        
        # Start hidden — the first status bar click will show the window.
        # Calling _do_show() here caused the window to appear briefly on launch
        # before the status bar icon was even drawn, which looked broken.
        self.is_visible = False

    def _do_toggle(self):
        if not self.window: return
        if self.is_visible:
            self.window.orderOut_(None)
            self.is_visible = False
        else:
            self._do_show()

    def run(self):
        try:
            self.ns_app = NSApplication.sharedApplication()
            self.delegate = AppDelegate.alloc().init()
            self.delegate.app_instance = self
            self.ns_app.setDelegate_(self.delegate)
            AppHelper.runEventLoop()
        except Exception:
            pass

if __name__ == "__main__":
    target_url = "https://gemini.google.com"
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
        
    app = CloakApp(target_url)
    app.run()
