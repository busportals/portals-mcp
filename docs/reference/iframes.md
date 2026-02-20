# Iframes

Iframes let you embed custom HTML/JS interfaces inside a Portals room. The system supports **bidirectional communication** — Portals can send data to iframes, and iframes can send commands back to the game engine.

Use cases: HUDs, mini-games, dialogue screens, inventory UIs, scoreboards, role reveals, maps, controls panels.

---

## Opening & Closing Iframes (Portals Side)

Three effects control iframes from the Portals interaction system:

| Effect | `$type` | Parameters | Purpose |
|--------|---------|------------|---------|
| Open Iframe | `IframeEvent` | `{"url": "iframe url"}` | Opens an iframe overlay |
| Close Iframe | `IframeStopEvent` | `{"iframeUrl": "iframe url"}` | Closes a specific iframe |
| Send Message | `SendMessageToIframes` | `{"iframeMsg": "text"}` | Sends text to all open iframes |

These work as standard effects — wrap them in `TaskTriggerSubscription` (basic) or `TaskEffectorSubscription` (quest-driven). See [interactions.md](interactions.md).

**Python helpers:**
```python
from portals_effects import effector_open_iframe, effector_close_iframe, effector_send_iframe_message

effector_open_iframe("https://example.com/hud.html", maximized=True, no_close_btn=True)
effector_close_iframe("https://example.com/hud.html")
effector_send_iframe_message("score: 42")
```

### URL Parameters

Append these to the iframe URL to control its appearance:

| Parameter | Effect |
|-----------|--------|
| `?noCloseBtn=true` | Hides the close button |
| `?hideMaximizeButton=true` | Hides the maximize button |
| `?hideRefreshButton=true` | Hides the refresh button |
| `?maximized=true` | Opens fullscreen |
| `?forceClose=true` | X button closes instead of minimizing |
| `?noBlur=true` | Disables background blur |
| `?height=300` | Sets iframe height in pixels |
| `?width=600` | Sets iframe width in pixels |
| `?left=10` | Sets iframe left offset |
| `?top=10` | Sets iframe top offset |

Combine multiple: `https://example.com/hud.html?maximized=true&noCloseBtn=true&hideRefreshButton=true`

---

## Portals SDK (HTML Side)

Every iframe that needs to communicate with Portals must load the SDK:

```html
<script src="https://portals-labs.github.io/portals-sdk/portals-sdk.js?v=10005456"></script>
```

Place this in `<head>` before any code that uses `PortalsSdk`.

### SDK Methods

| Method | Direction | Purpose |
|--------|-----------|---------|
| `PortalsSdk.sendMessageToUnity(jsonString)` | Iframe → Portals | Send commands to the game engine |
| `PortalsSdk.setMessageListener(callback)` | Portals → Iframe | Receive messages from `SendMessageToIframes` |
| `PortalsSdk.closeIframe()` | Iframe → Portals | Self-close the iframe |
| `PortalsSdk.focusGameKeyboard()` | Iframe → Portals | Return keyboard focus to the game |

---

## Iframe → Portals: Task State Changes

The primary use case for `sendMessageToUnity` is changing quest/task states from within HTML. The message must be a `JSON.stringify()`-ed object:

```javascript
PortalsSdk.sendMessageToUnity(JSON.stringify({
    TaskName: "quest-name",
    TaskTargetState: "SetActiveToCompleted"
}));
```

### TaskTargetState Values

| Value | From | To |
|-------|------|----|
| `ToNotActive` | Any | Not Active |
| `SetNotActiveToActive` | Not Active | Active |
| `SetActiveToCompleted` | Active | Completed |
| `SetCompletedToActive` | Completed | Active |
| `SetAnyToCompleted` | Any | Completed |
| `SetAnyToActive` | Any | Active |
| `SetActiveToNotActive` | Active | Not Active |
| `SetCompletedToNotActive` | Completed | Not Active |
| `SetNotActiveToCompleted` | Not Active | Completed |

**Important:** `TaskName` must **exactly match** the quest `Name` field (case-sensitive). These are the string equivalents of the numeric TargetState codes used in `RunTriggersFromEffector`.

### Complete Task Completion Pattern

```javascript
const Portals = {
    completeTask(taskName) {
        const message = JSON.stringify({
            TaskName: taskName,
            TaskTargetState: 'SetActiveToCompleted'
        });
        if (typeof PortalsSdk !== 'undefined') {
            PortalsSdk.sendMessageToUnity(message);
        }
    },

    closeIframe() {
        if (typeof PortalsSdk !== 'undefined') {
            PortalsSdk.closeIframe();
        }
    }
};

// Usage: complete task when player wins mini-game
if (score >= 100) {
    Portals.completeTask('0_minigame');
}
```

---

## Portals → Iframe: Receiving Messages

When `SendMessageToIframes` fires, all open iframes receive the message via `setMessageListener`:

```javascript
PortalsSdk.setMessageListener((message) => {
    console.log('Received from Portals:', message);
    // message is a raw text string
});
```

### Variable Interpolation

`SendMessageToIframes` supports pipe-delimited variables in the `iframeMsg` field:

| Variable | Resolves To |
|----------|-------------|
| `|username|` | Player's display name (quoted string) |
| `|position|` | Array of all player positions |
| `|variableName|` | Any variable set via `SetPlayersParameters` — returns object keyed by player name |

**Examples:**

| iframeMsg | Received by iframe |
|-----------|--------------------|
| `Hello |username|` | `Hello "PlayerName"` |
| `score: |score|` | `score: 42` |
| `role: |role|` | `role: {"Player1"="imposter", "Player2"="crewmate"}` |

**Parsing in the iframe:**
```javascript
PortalsSdk.setMessageListener((message) => {
    // Parse "key: value" format
    const match = message.match(/score\s*:\s*(\d+)/);
    if (match) {
        updateScoreDisplay(parseInt(match[1]));
    }
});
```

---

## Closing & Focus

### Self-Close from Iframe

```javascript
// Simple close
PortalsSdk.closeIframe();

// Animated close — delay to let CSS animation finish
function closeWithAnimation() {
    container.classList.add('fade-out');
    setTimeout(() => {
        PortalsSdk.closeIframe();
    }, 350);
}
```

### Return Keyboard Focus

After an iframe captures keyboard input (e.g., a text field), call this to return WASD/movement controls to the game:

```javascript
PortalsSdk.focusGameKeyboard();
```

---

## HTML Template

Minimal boilerplate for a Portals iframe:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>My Iframe</title>
    <script src="https://portals-labs.github.io/portals-sdk/portals-sdk.js?v=10005456"></script>
    <style>
        /* REQUIRED: transparent background for seamless embedding */
        html, body {
            margin: 0;
            padding: 0;
            background: transparent !important;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            color: white;
        }
    </style>
</head>
<body>
    <div id="app"></div>

    <script>
        // --- SDK availability check ---
        const sdk = typeof PortalsSdk !== 'undefined' ? PortalsSdk : null;

        // --- Receive messages from Portals ---
        if (sdk) {
            sdk.setMessageListener((message) => {
                console.log('Portals message:', message);
            });
        }

        // --- Send task state change to Portals ---
        function completeTask(taskName) {
            if (sdk) {
                sdk.sendMessageToUnity(JSON.stringify({
                    TaskName: taskName,
                    TaskTargetState: 'SetActiveToCompleted'
                }));
            }
        }

        // --- Close this iframe ---
        function close() {
            if (sdk) sdk.closeIframe();
        }
    </script>
</body>
</html>
```

---

## Compatibility

Iframes can be opened from any item type that supports effects:

| Item Type | Supported |
|-----------|-----------|
| Trigger Cube | Yes |
| ResizableCube | Yes |
| 9Cube (elemental) | Yes |
| GLB (custom import) | Yes |
| NPC | Yes (animates mouth with `NPC will animate` toggle) |

---

## Common Patterns

### HUD (always-on overlay)
Open on `OnPlayerLoggedIn` with `?maximized=true&noCloseBtn=true&hideMaximizeButton=true&hideRefreshButton=true`. Use `SendMessageToIframes` to push game state updates. Iframe receives and renders UI.

### Mini-Game
Open on trigger enter or click. Iframe runs the game logic. On completion, call `sendMessageToUnity` to complete a quest, then `closeIframe()`.

### Victory/Defeat Screen
Open via quest completion effect. Display results. Close button calls `closeIframe()`.

### Task Sheet / Inventory
Open on key press. Show/hide with CSS animations. Close with animated delay + `closeIframe()`.

### Parametric Loading
Pass data via URL query params: `game.html?task=3&difficulty=hard`. Parse with `URLSearchParams` in the iframe.

---

## Debugging

### Quick Checklist
- [ ] SDK script tag is in `<head>` before your code
- [ ] Using `JSON.stringify()` with `sendMessageToUnity` (not raw objects)
- [ ] `TaskName` exactly matches quest `Name` (case-sensitive)
- [ ] Testing inside Portals, not a standalone browser (SDK calls fail outside Portals)
- [ ] `html, body { background: transparent !important; }` for seamless embedding
- [ ] Set up `setMessageListener` before messages are sent

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `[object Object] is not a supported type` | Passed raw object to `sendMessageToUnity` | Use `JSON.stringify()` |
| `Failed to launch 'uniwebview://...'` | Testing in browser instead of Portals | Test inside Portals app |
| `Not allowed to launch 'uniwebview://'` | SDK call outside user gesture | Wrap in click/button handler |
| Messages not sending | TaskName mismatch | Check exact case-sensitive match |
| Messages not receiving | Listener not set up | Call `setMessageListener()` before messages fire |

### SDK Check
```javascript
if (typeof PortalsSdk !== 'undefined') {
    console.log('SDK loaded');
} else {
    console.log('Running outside Portals (dev mode)');
}
```

### Debug Iframe
Use this URL for testing message reception:
```
https://busportals.github.io/portals-games/iframe-debugger/?noBlur=true&height=300&left=10&top=10&width=600&hideCloseButton=true
```
