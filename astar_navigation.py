

import pygame
import math
import sys
from heapq import heappush, heappop

# ── Configuración ─────────────────────────────────────────────────────────────
ROWS, COLS = 18, 24
CELL_SIZE  = 36
SIDEBAR_W  = 220
MARGIN     = 16

WIN_W = COLS * CELL_SIZE + SIDEBAR_W + MARGIN * 3
WIN_H = ROWS * CELL_SIZE + MARGIN * 2 + 80

FPS = 60

# Colores
BG          = (2,   6,  23)
EMPTY_BG    = (30,  41,  59)
EMPTY_BD    = (51,  65,  85)
WALL_BG     = (15,  23,  42)
WALL_BD     = (30,  41,  59)
SLOW_BG     = (124, 58, 237)
SLOW_BD     = (109, 40, 217)
FAST_BG     = ( 3, 105, 161)
FAST_BD     = ( 2, 132, 199)
PATH_COL    = (244,  63,  94)
VISITED_COL = ( 30,  58,  95)
START_COL   = ( 34, 197,  94)
END_COL     = (245, 158,  11)
TEXT_COL    = (226, 232, 240)
MUTED_COL   = (100, 116, 139)
PANEL_BG    = (15,  23,  42)
PANEL_BD    = (30,  41,  59)
BTN_HOVER   = (51,  65,  85)

CELL_COLORS = {
    "empty": (EMPTY_BG, EMPTY_BD),
    "wall":  (WALL_BG,  WALL_BD),
    "slow":  (SLOW_BG,  SLOW_BD),
    "fast":  (FAST_BG,  FAST_BD),
}
TERRAIN_COST = {"empty": 1.0, "slow": 2.5, "fast": 0.5, "wall": None}

TOOLS = [
    ("start", "🚗  Origen",        START_COL),
    ("end",   "🏁  Destino",       END_COL),
    ("wall",  "🏢  Edificio",      (71, 85, 105)),
    ("slow",  "🐢  Tráfico lento", SLOW_BG),
    ("fast",  "⚡  Autopista",     FAST_BG),
    ("erase", "🗑   Borrar",       (51, 65, 85)),
]

# ── A* ────────────────────────────────────────────────────────────────────────
def heuristic(a, b):
    dx, dy = abs(a[0]-b[0]), abs(a[1]-b[1])
    return max(dx, dy) + (math.sqrt(2)-1) * min(dx, dy)

def astar(grid, start, end):
    rows, cols = len(grid), len(grid[0])
    open_heap = []
    heappush(open_heap, (0, start))
    came_from = {}
    g_score = {start: 0}
    visited = set()

    dirs = [
        (1,0,1),(-1,0,1),(0,1,1),(0,-1,1),
        (1,1,math.sqrt(2)),(-1,1,math.sqrt(2)),
        (1,-1,math.sqrt(2)),(-1,-1,math.sqrt(2)),
    ]

    while open_heap:
        _, current = heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path, visited

        cx, cy = current
        for dx, dy, cost in dirs:
            nx, ny = cx+dx, cy+dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            cell_type = grid[ny][nx]
            if cell_type == "wall":
                continue
            # No cortar esquinas
            if dx != 0 and dy != 0:
                if grid[cy][cx+dx] == "wall": continue
                if grid[cy+dy][cx] == "wall": continue

            terrain = TERRAIN_COST[cell_type]
            new_g = g_score[current] + cost * terrain
            neighbor = (nx, ny)
            if new_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = new_g
                f = new_g + heuristic(neighbor, end)
                heappush(open_heap, (f, neighbor))

    return [], visited

# ── App ───────────────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("🚗 Sistema de Navegación A*")
        self.clock = pygame.time.Clock()

        # Fuentes
        self.font_title = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font_ui    = pygame.font.SysFont("segoeui", 14)
        self.font_small = pygame.font.SysFont("segoeui", 12)
        self.font_emoji = pygame.font.SysFont("segoeuiemoji", 18)

        self.reset_all()

    def reset_all(self):
        self.grid   = [["empty"] * COLS for _ in range(ROWS)]
        self.start  = None
        self.end    = None
        self.path   = []
        self.visited= set()
        self.tool   = "start"
        self.animating    = False
        self.anim_index   = 0
        self.anim_timer   = 0
        self.full_path    = []
        self.status_msg   = "Selecciona Origen en el panel y haz clic en el mapa"
        self.status_color = END_COL
        self.mouse_down   = False

    def load_preset(self):
        self.reset_all()
        for y in range(2, 16): self.grid[y][6] = self.grid[y][7] = "wall"
        for y in range(4, 14): self.grid[y][14] = self.grid[y][15] = "wall"
        for x in range(3, 10): self.grid[5][x] = "wall"
        for x in range(9, 18): self.grid[10][x] = "wall"
        for x in range(8, 16): self.grid[3][x] = "fast"
        for y in range(12,16):
            for x in range(8,14): self.grid[y][x] = "slow"
        self.start = (1, 1)
        self.end   = (22, 16)
        self.status_msg   = "Ejemplo cargado — pulsa Calcular Ruta"
        self.status_color = FAST_BG

    def cell_rect(self, x, y):
        ox = MARGIN
        oy = MARGIN + 50
        return pygame.Rect(ox + x*CELL_SIZE, oy + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def grid_pos(self, mx, my):
        ox = MARGIN
        oy = MARGIN + 50
        x = (mx - ox) // CELL_SIZE
        y = (my - oy) // CELL_SIZE
        if 0 <= x < COLS and 0 <= y < ROWS:
            return (x, y)
        return None

    def apply_tool(self, pos):
        x, y = pos
        if self.tool == "start":
            self.start = pos
        elif self.tool == "end":
            self.end = pos
        elif self.tool == "erase":
            self.grid[y][x] = "empty"
        else:
            self.grid[y][x] = self.tool

    def run_astar(self):
        if not self.start or not self.end or self.animating:
            return
        self.path = []
        self.visited = set()
        path, visited = astar(self.grid, self.start, self.end)
        self.visited = visited
        if not path:
            self.status_msg   = "⚠ No existe ruta entre los puntos"
            self.status_color = PATH_COL
            return
        self.full_path  = path
        self.anim_index = 0
        self.anim_timer = 0
        self.animating  = True
        self.status_msg = "Calculando ruta..."
        self.status_color = TEXT_COL

    def update_animation(self, dt):
        if not self.animating:
            return
        self.anim_timer += dt
        if self.anim_timer >= 25:
            self.anim_timer = 0
            self.anim_index += 1
            self.path = self.full_path[:self.anim_index]
            if self.anim_index >= len(self.full_path):
                self.animating = False
                diag = sum(
                    1 for i in range(1, len(self.full_path))
                    if abs(self.full_path[i][0]-self.full_path[i-1][0]) == 1
                    and abs(self.full_path[i][1]-self.full_path[i-1][1]) == 1
                )
                self.status_msg   = f"✅ Ruta: {len(self.full_path)-1} pasos  |  {diag} diagonales  |  {len(self.visited)} celdas exploradas"
                self.status_color = START_COL

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill(BG)
        self.draw_title()
        self.draw_grid()
        self.draw_sidebar()
        self.draw_status()
        pygame.display.flip()

    def draw_title(self):
        surf = self.font_title.render("Sistema de Navegacion A*  —  AutomotechAI", True, TEXT_COL)
        self.screen.blit(surf, (MARGIN, MARGIN + 12))

    def draw_grid(self):
        path_set    = set(self.path)
        ox = MARGIN
        oy = MARGIN + 50

        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(ox + x*CELL_SIZE, oy + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pos  = (x, y)
                ctype = self.grid[y][x]
                bg, bd = CELL_COLORS[ctype]

                if pos in path_set:    bg = PATH_COL
                elif pos in self.visited: bg = VISITED_COL
                if pos == self.start:  bg = START_COL
                if pos == self.end:    bg = END_COL

                pygame.draw.rect(self.screen, bg, rect)
                pygame.draw.rect(self.screen, bd, rect, 1)

                # Emoji icons
                if pos == self.start:
                    self._draw_text("🚗", rect.centerx, rect.centery, self.font_emoji, (255,255,255), center=True)
                elif pos == self.end:
                    self._draw_text("🏁", rect.centerx, rect.centery, self.font_emoji, (255,255,255), center=True)
                elif pos == self.path[-1] if self.path else False:
                    self._draw_text("★", rect.centerx, rect.centery, self.font_ui, (255,220,50), center=True)

    def draw_sidebar(self):
        sx = COLS * CELL_SIZE + MARGIN * 2
        sy = MARGIN + 50

        # Panel background
        panel = pygame.Rect(sx, MARGIN, SIDEBAR_W, WIN_H - MARGIN*2 - 40)
        pygame.draw.rect(self.screen, PANEL_BG, panel, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_BD, panel, 1, border_radius=10)

        y = sy

        # Tools section
        self._draw_text("HERRAMIENTAS", sx+12, y, self.font_small, MUTED_COL)
        y += 22
        self.btn_rects = {}
        for tool_id, label, color in TOOLS:
            btn = pygame.Rect(sx+8, y, SIDEBAR_W-16, 32)
            is_active = self.tool == tool_id
            bg = (*color[:3],) if is_active else BTN_HOVER if btn.collidepoint(pygame.mouse.get_pos()) else PANEL_BG
            pygame.draw.rect(self.screen, bg, btn, border_radius=7)
            if is_active:
                pygame.draw.rect(self.screen, color, btn, 2, border_radius=7)
            self._draw_text(label, btn.x+10, btn.centery, self.font_ui, TEXT_COL, center_y=True)
            self.btn_rects[tool_id] = btn
            y += 36

        y += 8
        # Legend
        self._draw_text("LEYENDA", sx+12, y, self.font_small, MUTED_COL)
        y += 20
        legend = [
            (START_COL,   "Origen"),
            (END_COL,     "Destino"),
            (PATH_COL,    "Ruta óptima"),
            (SLOW_BG,     "Tráfico lento"),
            (FAST_BG,     "Autopista"),
            (WALL_BG,     "Edificio"),
            (VISITED_COL, "Explorado"),
        ]
        for color, label in legend:
            pygame.draw.rect(self.screen, color, (sx+12, y+2, 13, 13), border_radius=3)
            pygame.draw.rect(self.screen, PANEL_BD, (sx+12, y+2, 13, 13), 1, border_radius=3)
            self._draw_text(label, sx+32, y, self.font_small, TEXT_COL)
            y += 18

        y += 10
        # Action buttons
        actions = [
            ("run",    "▶ Calcular Ruta", START_COL),
            ("clear",  "↺ Limpiar Ruta",  (71,85,105)),
            ("preset", "🗺 Cargar Ejemplo", FAST_BG),
            ("reset",  "🗑 Reset Total",   PATH_COL),
        ]
        self.action_rects = {}
        for act_id, label, color in actions:
            btn = pygame.Rect(sx+8, y, SIDEBAR_W-16, 30)
            hover = btn.collidepoint(pygame.mouse.get_pos())
            bg = tuple(min(255, c+30) for c in color) if hover else color
            pygame.draw.rect(self.screen, bg, btn, border_radius=7)
            self._draw_text(label, btn.centerx, btn.centery, self.font_ui, (255,255,255), center=True)
            self.action_rects[act_id] = btn
            y += 36

        # Stats
        if self.full_path and not self.animating:
            y += 8
            self._draw_text("ESTADÍSTICAS", sx+12, y, self.font_small, MUTED_COL)
            y += 20
            diag = sum(
                1 for i in range(1, len(self.full_path))
                if abs(self.full_path[i][0]-self.full_path[i-1][0])==1
                and abs(self.full_path[i][1]-self.full_path[i-1][1])==1
            )
            stats = [
                ("Pasos:",      str(len(self.full_path)-1)),
                ("Exploradas:", str(len(self.visited))),
                ("Diagonales:", str(diag)),
            ]
            for label, val in stats:
                self._draw_text(label, sx+12, y, self.font_small, MUTED_COL)
                self._draw_text(val, sx+SIDEBAR_W-12, y, self.font_small, TEXT_COL, right=True)
                y += 17

    def draw_status(self):
        sy = MARGIN + 50 + ROWS * CELL_SIZE + 8
        surf = self.font_small.render(self.status_msg, True, self.status_color)
        self.screen.blit(surf, (MARGIN, sy))

    def _draw_text(self, text, x, y, font, color, center=False, center_y=False, right=False):
        surf = font.render(text, True, color)
        rx = x - surf.get_width()//2 if center else (x - surf.get_width() if right else x)
        ry = y - surf.get_height()//2 if (center or center_y) else y
        self.screen.blit(surf, (rx, ry))

    # ── Event handling ────────────────────────────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_down = True
                self.handle_click(event.pos)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_down = False

            if event.type == pygame.MOUSEMOTION and self.mouse_down:
                pos = self.grid_pos(*event.pos)
                if pos and self.tool not in ("start", "end"):
                    self.apply_tool(pos)
                    self.path = []; self.visited = set()
                    self.full_path = []; self.animating = False

    def handle_click(self, mpos):
        # Tool buttons
        for tool_id, btn in self.btn_rects.items():
            if btn.collidepoint(mpos):
                self.tool = tool_id
                return

        # Action buttons
        for act_id, btn in self.action_rects.items():
            if btn.collidepoint(mpos):
                if act_id == "run":    self.run_astar()
                elif act_id == "clear":
                    self.path=[]; self.visited=set(); self.full_path=[]; self.animating=False
                    self.status_msg="Ruta limpiada"; self.status_color=MUTED_COL
                elif act_id == "preset": self.load_preset()
                elif act_id == "reset":  self.reset_all()
                return

        # Grid click
        pos = self.grid_pos(*mpos)
        if pos:
            self.apply_tool(pos)
            self.path=[]; self.visited=set(); self.full_path=[]; self.animating=False
            if not self.start:
                self.status_msg="Selecciona Origen"; self.status_color=END_COL
            elif not self.end:
                self.status_msg="Selecciona Destino"; self.status_color=END_COL
            else:
                self.status_msg="Pulsa ▶ Calcular Ruta"; self.status_color=MUTED_COL

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update_animation(dt)
            self.draw()


if __name__ == "__main__":
    App().run()
