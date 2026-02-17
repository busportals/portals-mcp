"""
Portals Core Item Generators
Provides functions to create all standard Portals item types.

All item creators return (item_dict, logic_dict) tuples. Items contain
spatial/visual properties. Logic contains behavioral properties (interactions,
type-specific config).

Usage:
    items = {}
    logic = {}

    id_ = next_id()
    items[id_], logic[id_] = create_cube(pos=(0, 0.5, 0), color="FF0000")
"""

from typing import Dict, Tuple, Optional


def create_base_item(
    prefab_name: str,
    pos: Tuple[float, float, float] = (0, 0, 0),
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1),
    scale: Tuple[float, float, float] = (1, 1, 1),
    content_string: str = ""
) -> Dict:
    """
    Create base item structure that all Portals items share.

    Args:
        prefab_name: Item type (e.g., "ResizableCube", "WorldText", "Portal")
        pos: World position (x, y, z)
        rot: Quaternion rotation (qx, qy, qz, qw). Default is identity (no rotation)
        scale: Scale (x, y, z)
        content_string: URL or room ID depending on item type

    Returns:
        Item dict with spatial/visual properties (no extraData)
    """
    return {
        "prefabName": prefab_name,
        "parentItemID": 0,
        "currentEditornetId": 0,
        "pos": {"x": pos[0], "y": pos[1], "z": pos[2]},
        "modelsize": {"x": 0, "y": 0, "z": 0},
        "modelCenter": {"x": 0, "y": 0, "z": 0},
        "rot": {"x": rot[0], "y": rot[1], "z": rot[2], "w": rot[3]},
        "scale": {"x": scale[0], "y": scale[1], "z": scale[2]},
        "contentString": content_string,
        "interactivityType": 0,
        "interactivityURL": "",
        "hoverTitle": "",
        "hoverBodyContent": "",
        "ImageInteractivityDetails": {"buttonText": "", "buttonURL": ""},
        "sessionData": "",
        "instanceId": "",
        "placed": True,
        "locked": False,
        "superLocked": False
    }


def create_cube(
    pos: Tuple[float, float, float],
    scale: Tuple[float, float, float] = (1, 1, 1),
    color: str = "888888",
    emission: float = 0.0,
    opacity: float = 1.0,
    texture: str = "",
    collider: bool = True,
    shadows: bool = True,
    nav_mesh: bool = False,
    title: str = ""
) -> Tuple[Dict, Dict]:
    """
    Create a ResizableCube - the primary building block.

    Args:
        pos: World position (x, y, z). Ground is y=0, cube on ground has center at y=0.5
        scale: Dimensions (x, y, z). Default (1,1,1) = 1x1x1 cube
        color: 6-char hex color (no # prefix). e.g., "FF0000" for red
        emission: Glow intensity (0.0+). 0.0 = no glow, 1.0 = full glow
        opacity: Transparency (0.0-1.0). 1.0 = opaque, 0.0 = invisible
        texture: Image URL for texture. Empty = use solid color
        collider: True = solid (player collides), False = players pass through
        shadows: True = casts/receives shadows, False = no shadows (better FPS)
        nav_mesh: True = AI walkable surface for NPCs, False = not walkable
        title: Internal label for identification (not visible in-world)

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "col": color,
        "Tasks": [],
        "ViewNodes": []
    }

    if emission > 0:
        logic["e"] = emission
    if opacity < 1.0:
        logic["o"] = opacity
    if not collider:
        logic["c"] = False
    if not shadows:
        logic["s"] = False
    if nav_mesh:
        logic["nav"] = True
    if title:
        logic["title"] = title

    item = create_base_item(
        prefab_name="ResizableCube",
        pos=pos,
        scale=scale,
        content_string=texture
    )
    return (item, logic)


def create_text(
    pos: Tuple[float, float, float],
    content: str,
    billboard: bool = True,
    scale: Tuple[float, float, float] = (1, 1, 1)
) -> Tuple[Dict, Dict]:
    """
    Create WorldText - 3D text label with rich formatting.

    Args:
        pos: World position (x, y, z)
        content: Text string. Supports rich text tags:
            - <b>bold</b>
            - <i>italic</i>
            - <color=#FF0000>red text</color>
        billboard: True = always faces camera, False = fixed rotation
        scale: Scale (x, y, z)

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "text": content,
        "lookAtCamera": billboard,
        "Tasks": [],
        "ViewNodes": []
    }

    item = create_base_item(
        prefab_name="WorldText",
        pos=pos,
        scale=scale
    )
    return (item, logic)


def create_spawn(
    pos: Tuple[float, float, float],
    name: str = "",
    rotation_offset: float = 0.0
) -> Tuple[Dict, Dict]:
    """
    Create SpawnPoint - defines where players appear.

    Args:
        pos: World position (x, y, z). Typically y=0.2
        name: Spawn name. Empty "" = default spawn, any string = named spawn
        rotation_offset: Player facing direction offset in degrees. 0.0 = faces Z+

    Returns:
        (item_dict, logic_dict) tuple

    Notes:
        - Default spawn (name="") used when entering room or portal without spawn name
        - Named spawns referenced by Portal sn field
        - Scale always 0.3 for spawn points
        - Multiple spawns with same name = random assignment
    """
    logic = {
        "Tasks": [],
        "n": name,
        "r": rotation_offset
    }

    item = create_base_item(
        prefab_name="SpawnPoint",
        pos=pos,
        scale=(0.3, 0.3, 0.3)
    )
    return (item, logic)


def create_portal(
    pos: Tuple[float, float, float],
    scale: Tuple[float, float, float],
    destination_room_id: str,
    spawn_name: str = "",
    auto_teleport: bool = True
) -> Tuple[Dict, Dict]:
    """
    Create Portal - teleportation between rooms or spawn points.

    Args:
        pos: World position (x, y, z)
        scale: Portal size (x, y, z). Larger = easier to enter
        destination_room_id: Target room UUID
        spawn_name: Target spawn point name. Empty "" = default spawn
        auto_teleport: True = instant teleport on contact, False = press X

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "id": destination_room_id,
        "sn": spawn_name,
        "cm": "teleport",
        "Tasks": [],
        "ViewNodes": []
    }

    if auto_teleport:
        logic["auto"] = True

    item = create_base_item(
        prefab_name="Portal",
        pos=pos,
        scale=scale,
        content_string=destination_room_id
    )
    return (item, logic)


def create_collectible(
    pos: Tuple[float, float, float],
    glb_url: str,
    variable: str,
    value_change: int = 1,
    sound_url: str = "",
    display_value: bool = True,
    respawn_time: Optional[Tuple[float, float]] = None
) -> Tuple[Dict, Dict]:
    """
    Create Collectible GLB - pickupable item that modifies a variable.

    Args:
        pos: World position (x, y, z)
        glb_url: GLB model URL (will auto-append ?dynamic=true if not present)
        variable: Variable name to modify (e.g., "coins", "score")
        value_change: Amount to add. Default 1. Use negative for subtract
        sound_url: MP3 URL played on collection (optional)
        display_value: True = show UI with current value, False = silent collection
        respawn_time: Tuple (min_seconds, max_seconds) for random respawn delay

    Returns:
        (item_dict, logic_dict) tuple

    Notes:
        - Variable must be defined in room's variables array
        - GLB URL requires ?dynamic=true suffix
        - Scale defaults to (1,1,1) - adjust via return value if needed
    """
    # Ensure ?dynamic=true is in URL
    if "?dynamic=true" not in glb_url:
        glb_url += "?dynamic=true"

    logic = {
        "valueLabel": variable,
        "valueChange": value_change,
        "displayValue": display_value,
        "Tasks": [],
        "ViewNodes": []
    }

    if sound_url:
        logic["se"] = sound_url

    if respawn_time:
        logic["minRespawnTime"] = respawn_time[0]
        logic["maxRespawnTime"] = respawn_time[1]

    item = create_base_item(
        prefab_name="GlbCollectable",
        pos=pos,
        content_string=glb_url
    )
    return (item, logic)


def create_jump_pad(
    pos: Tuple[float, float, float],
    power: float = 6.9,
    scale: Tuple[float, float, float] = (1, 1, 1)
) -> Tuple[Dict, Dict]:
    """
    Create JumpPad - launches players into the air.

    Args:
        pos: World position (x, y, z). Typically y=0.5 for ground placement
        power: Launch power. Higher = more height. Reference:
            - 4.0-5.0 = small hop (1-2 meters)
            - 6.0-7.0 = medium jump (3-4 meters)
            - 8.0-10.0 = large jump (5+ meters)
            - 12.0+ = extreme launch
        scale: Pad size (x, y, z). Larger = easier to hit

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {"p": power}

    item = create_base_item(
        prefab_name="JumpPad",
        pos=pos,
        scale=scale
    )
    return (item, logic)


def create_trigger(
    pos: Tuple[float, float, float],
    scale: Tuple[float, float, float] = (1, 1, 1),
    press_button: bool = False,
    key_code: str = "X",
    message: str = ""
) -> Tuple[Dict, Dict]:
    """
    Create Trigger - invisible zone for interactions.

    Args:
        pos: World position (x, y, z)
        scale: Trigger size (x, y, z). Larger = easier to enter
        press_button: True = require key press, False = auto-trigger on enter
        key_code: Key to press (e.g., "X", "H", "E"). Only used if press_button=True
        message: Custom message shown as "Press [key] to [message]"

    Returns:
        (item_dict, logic_dict) tuple

    Notes:
        - Invisible during play (visible in build mode)
        - Two trigger types: User Enter and User Exit
        - Add effects via Tasks array (see portals_effects.py)
    """
    logic = {
        "events": [],
        "cm": message,
        "keyCode": key_code,
        "Tasks": [],
        "ViewNodes": []
    }

    if press_button:
        logic["pressBtn"] = True

    item = create_base_item(
        prefab_name="Trigger",
        pos=pos,
        scale=scale
    )
    return (item, logic)


def create_light(
    pos: Tuple[float, float, float],
    color: str = "FFFFFF",
    brightness: float = 2.0,
    range: float = 10.0,
    night_only: bool = False
) -> Tuple[Dict, Dict]:
    """
    Create Light - static point light source.

    Args:
        pos: World position (x, y, z). Typically elevated (y=3+)
        color: 6-char hex color (no # prefix)
        brightness: Light intensity. Higher = brighter
        range: How far the light reaches in meters
        night_only: True = only active in night mode

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "c": color,
        "b": brightness,
        "r": range,
        "Tasks": [],
        "ViewNodes": []
    }

    if night_only:
        logic["no"] = True

    item = create_base_item(prefab_name="Light", pos=pos)
    return (item, logic)


def create_spotlight(
    pos: Tuple[float, float, float],
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1),
    color: str = "FFFFFF",
    brightness: float = 2.0,
    range: float = 5.0,
    angle: float = 80.0
) -> Tuple[Dict, Dict]:
    """
    Create SpotLight - directional cone light.

    Args:
        pos: World position (x, y, z)
        rot: Quaternion rotation pointing the spotlight direction
        color: 6-char hex color (no # prefix)
        brightness: Light intensity
        range: How far the light reaches
        angle: Cone spread angle in degrees. Smaller = narrow beam

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "c": color,
        "b": brightness,
        "r": range,
        "ang": angle,
        "Tasks": [],
        "ViewNodes": []
    }

    item = create_base_item(prefab_name="SpotLight", pos=pos, rot=rot)
    return (item, logic)


def create_blink_light(
    pos: Tuple[float, float, float],
    color: str = "FFB200",
    brightness: float = 2.5,
    range: float = 7.0,
    blink_duration: float = 1.0,
    blink_interval: float = 2.0
) -> Tuple[Dict, Dict]:
    """
    Create BlinkLight - animated flashing light.

    Args:
        pos: World position (x, y, z)
        color: 6-char hex color (no # prefix)
        brightness: Light intensity
        range: How far the light reaches
        blink_duration: How long the light stays on (seconds)
        blink_interval: Time between blinks (seconds)

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "c": color,
        "b": brightness,
        "r": range,
        "bd": blink_duration,
        "bi": blink_interval,
        "Tasks": [],
        "ViewNodes": []
    }

    item = create_base_item(prefab_name="BlinkLight", pos=pos)
    return (item, logic)


def create_npc(
    pos: Tuple[float, float, float],
    glb_url: str,
    name: str,
    personality: str = "",
    animation: str = "",
    auto_popup: bool = True,
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1)
) -> Tuple[Dict, Dict]:
    """
    Create NPC - interactive character with dialogue and AI.

    Args:
        pos: World position (x, y, z). NPCs sit on ground at y=0
        glb_url: GLB model URL. Append ?nonrigged=true for static models
        name: NPC display name
        personality: AI personality prompt. Players can chat with NPC when set
        animation: Default animation. Options: Sitting, Can Can, Wave, Salute,
                   Jive, Salsa, Shuffling, Chicken, Slide n Jive, Robot.
                   Empty string "" for idle
        auto_popup: True = dialogue appears when player approaches
        rot: Quaternion rotation

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "n": name,
        "a": animation,
        "p": personality,
        "bq": True,
        "swn": auto_popup,
        "events": [],
        "tags": [],
        "Tasks": [],
        "ViewNodes": []
    }

    item = create_base_item(
        prefab_name="GLBNPC",
        pos=pos,
        rot=rot,
        content_string=glb_url
    )
    return (item, logic)


def create_glb(
    pos: Tuple[float, float, float],
    glb_url: str,
    scale: Tuple[float, float, float] = (1, 1, 1),
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1),
    shadows: bool = True,
    collider: bool = True
) -> Tuple[Dict, Dict]:
    """
    Create GLB - custom 3D model.

    Args:
        pos: World position (x, y, z)
        glb_url: GLB model URL (publicly accessible)
        scale: Proportional multiplier on native model size
        rot: Quaternion rotation
        shadows: True = casts shadows, False = no shadows (better FPS)
        collider: True = solid, False = players pass through

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {"Tasks": [], "ViewNodes": []}

    if not shadows:
        logic["s"] = False
    if not collider:
        logic["c"] = False

    item = create_base_item(
        prefab_name="GLB",
        pos=pos,
        rot=rot,
        scale=scale,
        content_string=glb_url
    )
    return (item, logic)


def create_image(
    pos: Tuple[float, float, float],
    image_url: str,
    scale: Tuple[float, float, float] = (2, 1.5, 0.03),
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1),
    transparent: bool = False,
    borderless: bool = False,
    emission: float = 0.0
) -> Tuple[Dict, Dict]:
    """
    Create Image - 2D image in 3D space.

    Args:
        pos: World position (x, y, z)
        image_url: Publicly hosted image URL
        scale: (width, height, thickness). Keep z thin (0.03)
        rot: Quaternion rotation. NOTE: images lie flat by default --
             use quaternion_from_euler(pitch=90) from portals_utils to stand upright
        transparent: True = respect PNG transparency
        borderless: True = no frame around image
        emission: Glow intensity. 0.0 = none

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {"Tasks": [], "ViewNodes": []}

    if transparent:
        logic["t"] = True
    if borderless:
        logic["b"] = True
    if emission > 0:
        logic["e"] = emission

    item = create_base_item(
        prefab_name="DefaultPainting",
        pos=pos,
        rot=rot,
        scale=scale,
        content_string=image_url
    )
    return (item, logic)


def create_video(
    pos: Tuple[float, float, float],
    video_url: str,
    scale: Tuple[float, float, float] = (3, 1.7, 0.03),
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1),
    borderless: bool = False,
    emission: float = 0.0
) -> Tuple[Dict, Dict]:
    """
    Create Video - MP4 video in 3D space. Displays upright by default.

    Args:
        pos: World position (x, y, z)
        video_url: MP4 video URL (publicly accessible)
        scale: (width, height, thickness). Keep z thin (0.03)
        rot: Quaternion rotation. Videos are upright by default (unlike images)
        borderless: True = no frame around video
        emission: Glow intensity. 0.0 = none

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {"Tasks": [], "ViewNodes": []}

    if borderless:
        logic["b"] = True
    if emission > 0:
        logic["e"] = emission

    item = create_base_item(
        prefab_name="DefaultVideo",
        pos=pos,
        rot=rot,
        scale=scale,
        content_string=video_url
    )
    return (item, logic)


def create_gun(
    pos: Tuple[float, float, float],
    weapon_type: int = 1,
    max_damage: int = 20,
    min_damage: int = 10,
    firerate: float = 0.5,
    clip_size: int = 12,
    infinite_ammo: bool = False,
    automatic: bool = False,
    color: str = "000000"
) -> Tuple[Dict, Dict]:
    """
    Create Gun - pickupable weapon.

    Args:
        pos: World position (x, y, z)
        weapon_type: 1 = Pistol, 2 = Rifle, 3 = Shotgun
        max_damage: Damage at close range
        min_damage: Damage at long range
        firerate: Time between shots (seconds). Lower = faster
        clip_size: Magazine capacity
        infinite_ammo: True = never runs out
        automatic: True = hold to fire continuously
        color: Gun model color (6-char hex, no #)

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "weaponType": weapon_type,
        "maxDamage": max_damage,
        "minDamage": min_damage,
        "firerate": firerate,
        "clipSize": clip_size,
        "startLoaded": True,
        "autoReload": True,
        "gunColor": color,
        "Tasks": [],
        "ViewNodes": []
    }

    if infinite_ammo:
        logic["isInfinityAmmo"] = True
    if automatic:
        logic["automaticWeapon"] = True

    item = create_base_item(prefab_name="Gun", pos=pos)
    return (item, logic)


def create_destructible(
    pos: Tuple[float, float, float],
    glb_url: str,
    scale: Tuple[float, float, float] = (1, 1, 1),
    max_health: int = 100,
    respawn_time: float = 10.0,
    multiplayer: bool = False
) -> Tuple[Dict, Dict]:
    """
    Create Destructible - 3D model that can be destroyed by weapons.

    Args:
        pos: World position (x, y, z)
        glb_url: GLB model URL
        scale: Proportional multiplier on native model size
        max_health: Health points before destruction
        respawn_time: Seconds before respawn after destruction
        multiplayer: True = shared destruction state across players

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "maxHealth": max_health,
        "respawnTime": respawn_time,
        "destructionEffect": {
            "particleCount": 40,
            "minParticleSize": 0.01,
            "maxParticleSize": 0.4,
            "minParticleSpeed": 1.0,
            "maxParticleSpeed": 6.0,
            "particleLifetime": 5.0,
            "radius": 2.0
        },
        "particleOrigin": {"rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
        "healthBarPos": {"position": [0, 2, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
        "Tasks": [],
        "ViewNodes": []
    }

    if multiplayer:
        logic["multiplayer"] = True

    item = create_base_item(
        prefab_name="Destructible",
        pos=pos,
        scale=scale,
        content_string=glb_url
    )
    return (item, logic)


def create_elemental(
    pos: Tuple[float, float, float],
    element_type: str = "lava",
    scale: Tuple[float, float, float] = (1, 1, 1),
    collider: bool = True
) -> Tuple[Dict, Dict]:
    """
    Create Elemental Cube - animated elemental block (lava, water).

    Args:
        pos: World position (x, y, z)
        element_type: "lava", "hotlava", or "water"
        scale: Cube dimensions
        collider: True = solid, False = pass through

    Returns:
        (item_dict, logic_dict) tuple
    """
    logic = {
        "GLBUrl": "https://dwh7ute75zx34.cloudfront.net/Models/08_09/9SliceBlock_Rig_Empty.glb",
        "c": "",
        "Tasks": [],
        "ViewNodes": []
    }

    if not collider:
        logic["nc"] = True

    item = create_base_item(
        prefab_name="9Cube",
        pos=pos,
        scale=scale,
        content_string=element_type
    )
    return (item, logic)


def create_addressable(
    pos: Tuple[float, float, float],
    effect_name: str,
    scale: Tuple[float, float, float] = (1, 1, 1),
    rot: Tuple[float, float, float, float] = (0, 0, 0, 1)
) -> Tuple[Dict, Dict]:
    """
    Create Addressable VFX - built-in particle/visual effects.

    Args:
        pos: World position (x, y, z). Typically y=0.5 for ground-level effects
        effect_name: Effect identifier WITHOUT prefix. e.g., "Fire2", "DustParticles".
            The "FurnitureAddressables/" prefix is added automatically.
        scale: Scale multiplier for the particle system
        rot: Quaternion rotation

    Returns:
        (item_dict, logic_dict) tuple

    Known effect names (not exhaustive):
        Particles: DustParticles, ParticlesExplosion1-5
        Fire: Fire, Fire1-3, FireBall1
        Explosion: ExplosionBomb1-7, ExplosionRing1, ExplosionRings2-3,
                   MagneticExplosion, NuclearExplosion, ShockExplosion,
                   SmokeExplosion1-2, WavesExplosion
        Lightning: LightningBall1, LightningExplosion1-3, LightningParticlesTree,
                   LightningShock1, LightningStrike1, LightningWave3, LightningWaves2
        Energy: AtomBall1-2
        Other: LineWaves1, Portal
    """
    content_string = f"FurnitureAddressables/{effect_name}"

    logic = {"Tasks": [], "ViewNodes": []}

    item = create_base_item(
        prefab_name="Addressable",
        pos=pos,
        rot=rot,
        scale=scale,
        content_string=content_string
    )
    return (item, logic)


def create_leaderboard(
    pos: Tuple[float, float, float],
    game_name: str,
    score_label: str = "Score",
    time_based: bool = False,
    style: str = "blue"
) -> Tuple[Dict, Dict]:
    """
    Create Leaderboard - displays player rankings.

    Args:
        pos: World position (x, y, z). Typically y=0.75 for ground placement
        game_name: Game name displayed on leaderboard
        score_label: Label for score column (e.g., "Points", "Time", "Coins")
        time_based: True = displays times, False = displays numeric scores
        style: "blue", "orange", or "screen"

    Returns:
        (item_dict, logic_dict) tuple
    """
    styles = {
        "blue": "~1slpk_Leaderboard_Black_NeonBlue.glb?alt=media&token=8b518415-b51b-4264-ae7e-d49465260757",
        "orange": "~5wnot_Leaderboard_Gray_NeonOrange.glb?alt=media&token=5312ebfe-b00b-4f99-ad4b-a72bd518a74a",
        "screen": "https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2F00L_screenLeaderboard.glb?alt=media&token=b1f9eef5-ee70-4d5e-a9ee-3e8e2ef26e59?screenOnly=true"
    }

    logic = {
        "gn": game_name,
        "ln": score_label,
        "ci": "",
        "Tasks": [],
        "ViewNodes": []
    }

    if time_based:
        logic["tb"] = True

    item = create_base_item(
        prefab_name="Leaderboard",
        pos=pos,
        content_string=styles.get(style, styles["blue"])
    )
    return (item, logic)
