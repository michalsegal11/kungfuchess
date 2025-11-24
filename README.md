סבבה, בואי נעשה את זה חד וברור 😊

### מה להעתיק ל-`README.md`?

1. בתיקיית השורש של הפרויקט (איפה שיש `client`, `server`, `assets` וכו’)
   צרי קובץ בשם **`README.md`**.
2. פתחי אותו והדביקי **בדיוק** את כל הטקסט שמופיע בין שלושת ה־` ```markdown ` לבין ה־` ``` ` פה למטה.

כל מה שמועתק בפנים הוא **באנגלית בלבד** ומתאים לפרויקט שלך.

````markdown
# Kungfu Chess – Online Multiplayer (Python)

This project is an extended version of the classic **Kungfu Chess** idea,
implemented in Python with a **client–server architecture**:

- **Server**: headless authoritative game logic over WebSockets.
- **Client**: Pygame-based UI where each player controls their pieces using the keyboard.

The goal is to allow multiple players to play real-time chess-like matches with
smooth physics, animations, and clear keyboard controls, and to support multiple
independent games in parallel.

---

## Features

- **Real-time chess-like gameplay** (Kungfu style – pieces can move continuously).
- **Authoritative server**:
  - Manages the full game state (board, pieces, physics).
  - Receives commands from clients via WebSockets.
  - Broadcasts state snapshots and game events to all connected clients.
- **Pygame client UI**:
  - Renders the board, pieces, cursors and move history.
  - Shows current players (White / Black) and the game result.
- **Clear win condition**:
  - When a king is captured, the server emits `GameEnded`.
  - Clients freeze input and show a "Game Over" overlay.
- **Keyboard-based control for each player**:
  - Player 1 (White) uses **Arrow keys + Enter**.
  - Player 2 (Black) uses **WASD + Space**.
- Designed to be extended with:
  - Better lobby / room system.
  - More visual effects and sounds.
  - Automated tests for physics, moves and events.

---

## Project Structure

The core layout is:

```text
project-root/
├─ client/
│  ├─ main.py           # Pygame main loop (client)
│  ├─ net.py            # WebSocket client (connects to server)
│  ├─ model.py          # Client-side game model (board + pieces projection)
│  ├─ input_handler.py  # Translates keyboard input to Commands
│  └─ graphics/         # Graphics helpers and sprite handling
│
├─ server/
│  ├─ main.py           # Headless WebSocket server (game logic only)
│  ├─ core/             # Logic modules re-used by both client/server
│  │   ├─ engine/       # Board, physics, states, events, commands
│  │   └─ pieces/       # Piece types, factory, movement rules
│  └─ graphics_stub.py  # Minimal stubs so server can import graphics modules
│
├─ assets/
│  └─ board.csv         # Initial board layout (piece codes per cell)
│
├─ pieces/              # Sprite folders per piece + per state
├─ snd/                 # Sound effects (optional)
├─ README.md
└─ .gitignore
````

> Note: The exact structure may vary slightly depending on how you organize
> your `core`, `server` and `client` packages, but the idea is the same.

---

## Requirements

* **Python** 3.11+
* Recommended packages (see `requirements.txt` if present):

  * `websockets`
  * `pygame`

Install dependencies (inside your virtual environment):

```bash
pip install -r requirements.txt
```

or, if you do not have a `requirements.txt` yet:

```bash
pip install websockets pygame
```

---

## Running the Application

### 1. Start the server

From the project root:

```bash
python -m server.main
```

You should see something like:

```text
🏁 Kungfu-Chess server listening on ws://127.0.0.1:8765
```

### 2. Start a client

In a **separate terminal**, again from the project root:

```bash
python -m client.main
```

The client will open a Pygame window. Depending on your implementation, the
client may ask for:

* Player name
* Desired color: `WHITE` or `BLACK`

### 3. Start a second client

Open another terminal and run:

```bash
python -m client.main
```

Choose the opposite color.
Once both `WHITE` and `BLACK` are connected, the server emits a `GameStarted`
event and the match begins.

---

## Controls

By default:

### White Player

* `↑` / `↓` / `←` / `→` – Move the selection cursor on the board.
* `Enter` – Select a piece on the current square or confirm a move/jump.

### Black Player

* `W` / `A` / `S` / `D` – Move the selection cursor.
* `Space` – Select a piece or confirm a move/jump.

> Movement and selection rules are validated by the server; illegal commands may
> produce error events (e.g. `ErrorPlayed`) that can be displayed in the UI.

---

## Game Flow

1. Both players connect to the server and choose colors.
2. The server initializes the board from `assets/board.csv` and constructs
   all pieces via `PieceFactory`.
3. Clients send `Command` objects (move / jump / capture) via WebSockets.
4. The server:

   * Applies physics and piece states in a tick loop.
   * Resolves collisions and captures.
   * Broadcasts `MovePlayed`, `PieceTaken`, `StateChanged` and other events.
5. Once a king is captured:

   * The server publishes `GameEnded(winner)`.
   * Clients set `game_over = True`, stop sending commands and show a
     "Game Over" overlay with the winner.

---

## Development Notes

* The **server** is the single source of truth for game state.
* The **client** keeps a projection of the board and reacts to events and
  state snapshots.
* Input is debounced and validated so that:

  * Pieces cannot be re-selected while moving.
  * Each player can only control their own color.

This design makes it easier to later add:

* Spectator clients.
* Multiple parallel games (lobby / room system).
* Replays and recorded game logs.

---

## How to Run Tests

> (If you have or plan to add tests, describe them here.)

For example:

```bash
pytest tests/
```

You can organize tests by module:

```text
tests/
├─ test_board.py
├─ test_physics.py
├─ test_pieces.py
└─ test_game_flow.py
```

---

## License

Add your preferred license here (MIT, Apache-2.0, etc.).

