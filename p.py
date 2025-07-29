from engine.Board import Board
from engine.Command import Command
from engine.State import State
from engine.Moves import Moves
import cv2



class Piece:
    def __init__(
        self,
        piece_id: str,
        init_state: State,
        moves: Moves | None = None,   # ←  חדש
    ):
        self.piece_id = piece_id
        self.current_state = init_state
        self.initial_state  = init_state


        # Piece.py  – בתוך __init__
        self.moves = init_state.moves        # הוסף שורה אחת

        # self.moves = moves     # ←  חדש
        
        # Timing
        self.last_command_time = 0
        self.creation_time = 0
        
        # Cooldown system
        self.cooldown_duration_ms = 1000  # Default 1 second cooldown
        self.last_action_time = 0
        
        # Status
        self.is_active = True
        self.is_captured = False

    def on_command(self, cmd: Command, now_ms: int):
        """Handle a command for this piece (only *Move* רלוונטי כאן)."""
        if self.is_captured:
            return                                              # כלי מת כבר

        # *Move* בלבד – הפרמטרים הם [(r0,c0), (r1,c1)]
        if cmd.type != "Move" or len(cmd.params) < 2:
            return

        from_cell, to_cell = cmd.params

        # 1️⃣  האם המהלך חוקי לפי moves.txt ?
        legal = self.current_state.moves.get_moves(*from_cell)
        if to_cell not in legal:
            return                                              # פסול → מתעלמים

        # 2️⃣  הפעל את ה‑State → Physics
        self.current_state.start_move(to_cell, now_ms)

        # 3️⃣  עדכון טיימרים פנימיים
        self.last_command_time = now_ms
        self.last_action_time  = now_ms


        # Check cooldown
        if now_ms - self.last_action_time < self.cooldown_duration_ms:
            return  # Still in cooldown
        
        # Process the command through state machine
        self.current_state = self.current_state.get_state_after_command(cmd, now_ms)
        self.last_command_time = now_ms
        
        # Update last action time if this was an action command
        if cmd.type in ["Move", "Capture", "Jump", "Attack"]:
            self.last_action_time = now_ms

    def reset(self, start_ms: int):
        """Reset the piece to idle state."""
        self.current_state = self.initial_state
        self.creation_time = start_ms
        self.last_command_time = start_ms
        self.last_action_time = 0
        self.is_active = True
        self.is_captured = False
        
        # Create a reset command
        reset_cmd = Command(
            timestamp=start_ms,
            piece_id=self.piece_id,
            type="Reset",
            params=[]
        )
        self.current_state.reset(reset_cmd)

    def update(self, now_ms: int):
        """Update the piece state based on current time."""
        if not self.is_active or self.is_captured:
            return
            
        # Update current state
        self.current_state = self.current_state.update(now_ms)

    # def draw_on_board(self, board: Board, now_ms: int):
    #     """Draw the piece on the board with cooldown overlay."""
    #     if not self.is_active or self.is_captured:
    #         return
        
    #     # Get current image and position from state
    #     try:
    #         img = self.current_state.get_current_image()
    #         pos = self.current_state.get_current_position()
            
    #         # Draw the piece
    #         if img and hasattr(img, 'draw_on'):
    #             img.draw_on(board.img, pos[0], pos[1])
            
    #         # Draw cooldown indicator if in cooldown
    #         self._draw_cooldown_indicator(board, now_ms, pos)
            
    #     except Exception as e:
    #         # Fallback: draw a simple indicator
    #         pos = self.current_state.get_current_position()
    #         self._draw_fallback_indicator(board, pos)




    def draw_on_board(self, board: "Board") -> None:
        """
        מצייר את הכלי על הלוח לפי המיקום הנוכחי שלו.
        """
        try:
            piece_img = self.current_state.get_current_image()
            piece_pos = self.current_state.get_current_position()

            if piece_img.img is None:
                return

            piece_height, piece_width = piece_img.img.shape[:2]
            draw_x = int(piece_pos[0] - piece_width / 2)
            draw_y = int(piece_pos[1] - piece_height / 2)

            # בדיקת גבולות
            img_height, img_width = board.img.img.shape[:2]
            margin = 5
            if (margin <= draw_x < img_width - piece_width - margin and
                margin <= draw_y < img_height - piece_height - margin):
                piece_img.draw_on(board.img, draw_x, draw_y)
            else:
                draw_x = max(margin, min(draw_x, img_width - piece_width - margin))
                draw_y = max(margin, min(draw_y, img_height - piece_height - margin))
                piece_img.draw_on(board.img, draw_x, draw_y)
        except Exception as e:
            print(f"[Error] Failed to draw piece {self.piece_id}: {e}")

            

    def _draw_fallback_indicator(self, board, now):
            # למשל, לצייר מסגרת אדומה סביב המיקום של הכלי
            pos = self.current_state.get_current_position()
            x, y = pos
            # נניח ש-board.img.img הוא numpy array עם תמונה
            # כאן תצייר מלבן קטן סביב המיקום, לדוגמה:

            cell_size = 50  # לדוגמה, גודל תא הלוח בפיקסלים - להתאים לפי הלוח שלך
            top_left = (x * cell_size, y * cell_size)
            bottom_right = ((x + 1) * cell_size - 1, (y + 1) * cell_size - 1)
            cv2.rectangle(board.img.img, top_left, bottom_right, (0, 0, 255), 2)  # אדום

    


    def _draw_cooldown_indicator(self, board: Board, now_ms: int, pos: tuple[int, int]):
        """Draw cooldown indicator if piece is in cooldown."""
        cooldown_remaining = self.cooldown_duration_ms - (now_ms - self.last_action_time)
        
        if cooldown_remaining > 0:
            # Calculate cooldown progress (0 to 1)
            progress = 1.0 - (cooldown_remaining / self.cooldown_duration_ms)
            
            # Convert board position to pixel coordinates (assuming cell size)
            cell_size = 50  # שנה בהתאם לגודל תא אצלך
            x_px = pos[0] * cell_size
            y_px = pos[1] * cell_size

            # Draw a rectangle showing cooldown progress
            bar_height = 5
            bar_width = int(cell_size * progress)
            cv2.rectangle(
                board.img.img,
                (x_px, y_px + cell_size - bar_height),
                (x_px + bar_width, y_px + cell_size),
                (0, 255, 0),  # Green
                -1  # Filled
            )

            # Optional: draw text with seconds remaining
            text = f"{cooldown_remaining // 1000 + 1}s"
            cv2.putText(
                board.img.img,
                text,
                (x_px + 2, y_px + cell_size - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1
            )
