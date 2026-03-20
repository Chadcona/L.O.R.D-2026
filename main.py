# Legend of the Red Dragon: 16-Bit Edition
# Main entry point — game loop, window setup, scene registration

import pygame
import sys
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    FPS, TITLE, BLACK
)
from scenes.scene_manager import SceneManager
from scenes.title_screen import TitleScreen
from scenes.char_create import CharCreateScene
from scenes.town import TownScene
from scenes.forest import ForestScene
from scenes.battle import BattleScene
from scenes.load_game import LoadGameScene


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    # Start windowed and resizable; track fullscreen state
    fullscreen = False
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE
    )
    virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    clock = pygame.time.Clock()

    # Initialize music system
    from systems.music import MusicManager
    music = MusicManager()

    # Register all scenes
    manager = SceneManager()
    manager.register("title", TitleScreen())
    manager.register("char_create", CharCreateScene())
    manager.register("town", TownScene())
    manager.register("forest", ForestScene())
    manager.register("battle", BattleScene())
    manager.register("load_game", LoadGameScene())

    # Start at title screen
    manager.switch_immediate("title")
    music.play("title")

    running = True
    prev_scene = None

    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            # Fullscreen toggle: F11 or Alt+Enter
            if event.type == pygame.KEYDOWN:
                toggle_fs = False
                if event.key == pygame.K_F11:
                    toggle_fs = True
                elif event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                    toggle_fs = True
                if toggle_fs:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            (0, 0), pygame.FULLSCREEN | pygame.SCALED
                        )
                    else:
                        screen = pygame.display.set_mode(
                            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE
                        )
                    continue

            # Handle custom timer events (enemy turn in battle)
            if event.type == pygame.USEREVENT + 1:
                scene = manager.scenes.get(manager.current_scene)
                if hasattr(scene, '_do_enemy_turn'):
                    scene._do_enemy_turn()
                continue

            manager.handle_event(event)

        if not running:
            break

        # Update music based on current scene
        cur_scene = manager.current_scene
        if cur_scene != prev_scene:
            scene_music = {
                "title": "title",
                "char_create": "title",
                "load_game": "title",
                "town": "town",
                "forest": "forest",
                "battle": "battle",
            }
            track = scene_music.get(cur_scene)
            if track:
                music.play(track)
            else:
                music.stop()
            prev_scene = cur_scene

        # Update
        manager.update(dt)

        # Draw to virtual screen, then scale up
        virtual_screen.fill(BLACK)
        manager.draw(virtual_screen)

        # Scale virtual screen to actual display with aspect ratio preservation
        screen.fill(BLACK)
        display_w, display_h = screen.get_size()
        # Calculate largest integer or fractional scale that fits
        scale = min(display_w / VIRTUAL_WIDTH, display_h / VIRTUAL_HEIGHT)
        scaled_w = int(VIRTUAL_WIDTH * scale)
        scaled_h = int(VIRTUAL_HEIGHT * scale)
        offset_x = (display_w - scaled_w) // 2
        offset_y = (display_h - scaled_h) // 2
        scaled = pygame.transform.scale(virtual_screen, (scaled_w, scaled_h))
        screen.blit(scaled, (offset_x, offset_y))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
