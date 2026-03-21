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

    # Start windowed; track fullscreen state
    fullscreen = False
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            (0, 0), pygame.FULLSCREEN | pygame.SCALED
                        )
                    else:
                        screen = pygame.display.set_mode(
                            (SCREEN_WIDTH, SCREEN_HEIGHT)
                        )
                    continue
                elif event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            (0, 0), pygame.FULLSCREEN | pygame.SCALED
                        )
                    else:
                        screen = pygame.display.set_mode(
                            (SCREEN_WIDTH, SCREEN_HEIGHT)
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
            if cur_scene == "title":
                music.play("title")
            elif cur_scene == "town":
                music.play("town")
            elif cur_scene in ("forest",):
                music.play("forest")
            elif cur_scene == "battle":
                music.play("battle")
            prev_scene = cur_scene

        # Update
        manager.update(dt)

        # Draw to virtual screen, then scale up
        virtual_screen.fill(BLACK)
        manager.draw(virtual_screen)

        # Scale virtual screen to actual display
        display_size = screen.get_size()
        scaled = pygame.transform.scale(virtual_screen, display_size)
        screen.blit(scaled, (0, 0))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
