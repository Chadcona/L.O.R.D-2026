# Scene Manager — handles scene transitions with fade effects

import pygame
from settings import BLACK, FPS


class SceneManager:
    """Manages game scenes and transitions between them."""

    def __init__(self):
        self.scenes = {}
        self.current_scene = None
        self.next_scene = None
        self.transitioning = False
        self.fade_alpha = 0
        self.fade_speed = 8
        self.fading_out = False
        self.transition_data = None

    def register(self, name, scene):
        """Register a scene by name."""
        self.scenes[name] = scene
        scene.manager = self

    def switch_to(self, name, data=None):
        """Begin a fade transition to a new scene."""
        if name not in self.scenes:
            raise ValueError(f"Scene '{name}' not registered")
        if self.transitioning:
            return
        self.next_scene = name
        self.transition_data = data
        self.transitioning = True
        self.fading_out = True
        self.fade_alpha = 0

    def switch_immediate(self, name, data=None):
        """Switch to a scene instantly (no fade)."""
        if name not in self.scenes:
            raise ValueError(f"Scene '{name}' not registered")
        if self.current_scene and hasattr(self.scenes.get(self.current_scene), 'on_exit'):
            self.scenes[self.current_scene].on_exit()
        self.current_scene = name
        scene = self.scenes[name]
        if hasattr(scene, 'on_enter'):
            scene.on_enter(data)

    def update(self, dt):
        """Update current scene and handle transitions."""
        if self.transitioning:
            if self.fading_out:
                self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
                if self.fade_alpha >= 255:
                    # Switch scene at peak of fade
                    if self.current_scene and hasattr(self.scenes.get(self.current_scene), 'on_exit'):
                        self.scenes[self.current_scene].on_exit()
                    self.current_scene = self.next_scene
                    scene = self.scenes[self.current_scene]
                    if hasattr(scene, 'on_enter'):
                        scene.on_enter(self.transition_data)
                    self.fading_out = False
            else:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
                if self.fade_alpha <= 0:
                    self.transitioning = False
                    self.next_scene = None
                    self.transition_data = None

        if self.current_scene:
            self.scenes[self.current_scene].update(dt)

    def draw(self, surface):
        """Draw current scene and fade overlay."""
        if self.current_scene:
            self.scenes[self.current_scene].draw(surface)

        if self.transitioning and self.fade_alpha > 0:
            fade_surface = pygame.Surface(surface.get_size())
            fade_surface.fill(BLACK)
            fade_surface.set_alpha(self.fade_alpha)
            surface.blit(fade_surface, (0, 0))

    def handle_event(self, event):
        """Pass events to current scene."""
        if self.transitioning:
            return
        if self.current_scene:
            self.scenes[self.current_scene].handle_event(event)


class Scene:
    """Base class for all game scenes."""

    def __init__(self):
        self.manager = None

    def on_enter(self, data=None):
        """Called when scene becomes active."""
        pass

    def on_exit(self):
        """Called when scene is being left."""
        pass

    def update(self, dt):
        """Update scene logic. dt = delta time in seconds."""
        pass

    def draw(self, surface):
        """Draw the scene to the virtual surface."""
        pass

    def handle_event(self, event):
        """Handle a pygame event."""
        pass
