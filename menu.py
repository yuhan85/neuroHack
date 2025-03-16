import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu")

font = pygame.font.Font(None, 36)

# 变量
countdown = 0
countdown_started = False
begin_game_button_visible = False

# 按钮尺寸和位置
button_width, button_height = 150, 60
start_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height // 2, button_width, button_height)
start_game_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height // 2, button_width, button_height)

def update_countdown():
    """更新倒计时"""
    global countdown, begin_game_button_visible
    if countdown > 0:
        screen.fill((0, 0, 0))
        countdown_text = font.render(f"Close your eyes and calm down in {countdown} seconds", True, (150, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2 - 100))
        pygame.display.update()
        pygame.time.delay(1000)
        countdown -= 1
    if countdown == 0:  # 倒计时结束，显示“Start Game”按钮
        begin_game_button_visible = True

def draw_menu():
    """绘制菜单界面"""
    screen.fill((0, 0, 0))

    if countdown_started and countdown > 0:
        update_countdown()
    elif begin_game_button_visible:  # 倒计时结束后，显示“Start Game”按钮
        pygame.draw.rect(screen, (50, 50, 50), start_game_button_rect)  # 按钮背景
        pygame.draw.rect(screen, (255, 255, 255), start_game_button_rect, 2)  # 按钮边框
        text = font.render("Start Game", True, (255, 255, 255))
        screen.blit(text, (start_game_button_rect.x + (button_width - text.get_width()) // 2,
                           start_game_button_rect.y + (button_height - text.get_height()) // 2))
    else:
        pygame.draw.rect(screen, (50, 50, 50), start_button_rect)  # 按钮背景
        pygame.draw.rect(screen, (255, 255, 255), start_button_rect, 2)  # 按钮边框
        text = font.render("Start", True, (255, 255, 255))
        screen.blit(text, (start_button_rect.x + (button_width - text.get_width()) // 2,
                           start_button_rect.y + (button_height - text.get_height()) // 2))

    pygame.display.update()

def handle_menu_events():
    """处理菜单事件"""
    global countdown_started, countdown, begin_game_button_visible

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if not countdown_started and start_button_rect.collidepoint(x, y):
                countdown_started = True
                countdown = 5  # 设定倒计时（可以调整）
            elif begin_game_button_visible and start_game_button_rect.collidepoint(x, y):
                start_game()  # 进入游戏

def start_game():
    """进入游戏（示例）"""
    print("游戏开始！")
    pygame.quit()
    sys.exit()

def main():
    """主循环"""
    while True:
        handle_menu_events()
        draw_menu()

if __name__ == "__main__":
    main()
