#!/usr/bin/env python3
"""
convert_colors.py

Replace English color words in a text file with other random English color words.

Usage:
  python convert_colors.py input.txt -o output.txt
  python convert_colors.py input.txt --inplace

Options:
  --seed N       Seed RNG for reproducible replacements
  --inplace      Overwrite input file
"""
import argparse
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


def _unescape_cpp_string(s: str) -> str:
    # Best-effort unescape for common sequences in C++ string literals.
    try:
        return s.encode("utf-8").decode("unicode_escape")
    except Exception:
        return s


def load_colors_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load COLORS by parsing ai.cpp's color vector.

    This keeps Python replacement colors exactly in sync with the C++ generator.
    """
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    # Find the const vector<string> color = { "a", "b", ... };
    m = re.search(
        r"const\s+std::vector<std::string>\s+color\s*=\s*\{(?P<list>.*?)\}\s*;",
        text,
        flags=re.DOTALL,
    )
    if not m:
        raise ValueError("Could not find color vector in ai.cpp")

    list_src = m.group("list")
    raw = re.findall(r'"((?:\\.|[^"\\])*)"', list_src)
    colors = [_unescape_cpp_string(s) for s in raw]

    if not colors:
        raise ValueError("color vector was empty")

    return colors


def load_material_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load MATERIAL by parsing ai.cpp's material vector."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    # Find the const vector<string> material = { "a", "b", ... };
    m = re.search(
        r"const\s+std::vector<std::string>\s+material\s*=\s*\{(?P<list>.*?)\}\s*;",
        text,
        flags=re.DOTALL,
    )
    if not m:
        raise ValueError("Could not find material vector in ai.cpp")

    list_src = m.group("list")
    raw = re.findall(r'"((?:\\.|[^"\\])*)"', list_src)
    material = [_unescape_cpp_string(s) for s in raw]

    if not material:
        raise ValueError("material vector was empty")

    return material


def load_maskcolor_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load MASKCOLOR by parsing ai.cpp's maskcolor vector."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    # Find the const vector<string> maskcolor = { "a", "b", ... };
    m = re.search(
        r"const\s+std::vector<std::string>\s+maskcolor\s*=\s*\{(?P<list>.*?)\}\s*;",
        text,
        flags=re.DOTALL,
    )
    if not m:
        raise ValueError("Could not find maskcolor vector in ai.cpp")

    list_src = m.group("list")
    raw = re.findall(r'"((?:\\.|[^"\\])*)"', list_src)
    maskcolor = [_unescape_cpp_string(s) for s in raw]

    if not maskcolor:
        raise ValueError("maskcolor vector was empty")

    return maskcolor


def load_mouthmask_material_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load mouthMaskMaterial by parsing ai.cpp's mouthMaskMaterial vector."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    # Find the const vector<string> mouthMaskMaterial = { "a", "b", ... };
    m = re.search(
        r"const\s+std::vector<std::string>\s+mouthMaskMaterial\s*=\s*\{(?P<list>.*?)\}\s*;",
        text,
        flags=re.DOTALL,
    )
    if not m:
        raise ValueError("Could not find mouthMaskMaterial vector in ai.cpp")

    list_src = m.group("list")
    raw = re.findall(r'"((?:\\.|[^"\\])*)"', list_src)
    mouthmask_material = [_unescape_cpp_string(s) for s in raw]

    if not mouthmask_material:
        raise ValueError("mouthMaskMaterial vector was empty")

    return mouthmask_material


def _extract_function_region(text: str, func_name: str) -> str:
    # Extract a region starting at `std::string <func_name>(...) {` up to the next
    # `std::string <something>(...)` definition or closing brace at function level.
    start_match = re.search(
        rf"\bstd::string\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{",
        text,
    )
    if not start_match:
        raise ValueError(f"Could not find {func_name}() in ai.cpp")

    # Find the end of this function by counting braces or finding the next function
    next_match = re.search(r"\nstd::string\s+\w+\s*\([^)]*\)\s*\{", text[start_match.end():])
    if not next_match:
        return text[start_match.start():]

    end_idx = start_match.end() + next_match.start()
    return text[start_match.start():end_idx]


@dataclass(frozen=True)
class CameraAngleOption:
    text: str
    must_have: tuple[str, ...] = ()
    must_not_have: tuple[str, ...] = ()


def _parse_output_find_conditions(cond: str) -> tuple[set[str], set[str]]:
    """Extract simple output.find("...") presence/absence checks.

    Supports:
      - output.find("X") != std::string::npos  -> must_have X
      - output.find("X") == std::string::npos  -> must_not_have X

    Anything more complex is ignored.
    """
    must_have: set[str] = set()
    must_not_have: set[str] = set()

    # Presence checks
    for s in re.findall(
        r'output\.find\(\s*"((?:\\.|[^"\\])*)"\s*\)\s*!=\s*(?:std::string::npos|npos)',
        cond,
    ):
        must_have.add(_unescape_cpp_string(s))

    # Absence checks
    for s in re.findall(
        r'output\.find\(\s*"((?:\\.|[^"\\])*)"\s*\)\s*==\s*(?:std::string::npos|npos)',
        cond,
    ):
        must_not_have.add(_unescape_cpp_string(s))

    return must_have, must_not_have


def _extract_fondle_target_values(text: str) -> list[str]:
    """Extract all possible fondleTarget values from assignments in ai.cpp."""
    values: set[str] = set()
    
    # Match direct assignment: fondleTarget = "value";
    for m in re.finditer(r'fondleTarget\s*=\s*"([^"]+)"\s*;', text):
        values.add(m.group(1))
    
    # Match pickRandomString assignment: fondleTarget = pickRandomString({...});
    for m in re.finditer(r'fondleTarget\s*=\s*pickRandomString\s*\(\s*\{([^}]+)\}\s*\)\s*;', text, re.DOTALL):
        list_content = m.group(1)
        # Extract quoted strings from the list
        for s in re.findall(r'"([^"]+)"', list_content):
            values.add(s)
    
    return sorted(values)


def _load_camera_angle_options_from_cpp(cpp_path: Path | None = None) -> list[CameraAngleOption]:
    """Load camera angle options by parsing ai.cpp's getShot() and its output.find(...) checks.

    We mirror the *output* gating logic in C++ by attaching simple presence/absence conditions
    to each angle that is directly pushed via newShot.push_back("...").
    """
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")
    region = _extract_function_region(text, "getShot")
    
    # Extract all possible fondleTarget values from the entire file
    fondle_targets = _extract_fondle_target_values(text)

    options: list[CameraAngleOption] = []

    # Walk the function while tracking brace depth and active conditions.
    depth = 0

    # Track if/else-if/else chains per brace depth, so we can apply implied negations for `else`.
    # Keyed by the brace depth where the chain's `if (...) {` begins.
    chains: dict[int, list[tuple[set[str], set[str]]]] = {}

    # Stack entries: (block_depth, must_have_set, must_not_have_set)
    cond_stack: list[tuple[int, set[str], set[str]]] = []

    i = 0
    n = len(region)

    def _skip_ws(pos: int) -> int:
        while pos < n and region[pos].isspace():
            pos += 1
        return pos

    def _try_parse_if_at(pos: int) -> tuple[str, int, bool] | None:
        """If an (else) if header starts at pos, return (cond, new_pos_after_open_brace, is_else_if)."""
        j = pos
        # Optional leading 'else'
        is_else_if = False
        if region.startswith("else", j) and (j + 4 == n or not region[j + 4].isalnum() and region[j + 4] != "_"):
            j += 4
            j = _skip_ws(j)
            is_else_if = True

        if not region.startswith("if", j) or (j + 2 < n and (region[j + 2].isalnum() or region[j + 2] == "_")):
            return None
        j += 2
        j = _skip_ws(j)
        if j >= n or region[j] != "(":
            return None

        # Parse condition with balanced parentheses, respecting string literals.
        j += 1
        cond_start = j
        paren_depth = 1
        in_str = False
        while j < n:
            ch = region[j]
            if in_str:
                if ch == "\\":
                    j += 2
                    continue
                if ch == '"':
                    in_str = False
                j += 1
                continue
            else:
                if ch == '"':
                    in_str = True
                    j += 1
                    continue
                if ch == "(":
                    paren_depth += 1
                elif ch == ")":
                    paren_depth -= 1
                    if paren_depth == 0:
                        cond_end = j
                        j += 1
                        break
                j += 1

        else:
            return None

        cond = region[cond_start:cond_end]
        j = _skip_ws(j)
        if j >= n or region[j] != "{":
            return None
        j += 1
        return cond, j, is_else_if

    def _try_parse_else_block_at(pos: int) -> int | None:
        j = pos
        if not region.startswith("else", j) or (j + 4 < n and (region[j + 4].isalnum() or region[j + 4] == "_")):
            return None
        j += 4
        j = _skip_ws(j)
        if j >= n or region[j] != "{":
            return None
        return j + 1

    while i < n:
        # Skip // comments
        if region.startswith("//", i):
            j = region.find("\n", i)
            if j == -1:
                break
            i = j + 1
            continue

        # Skip /* */ comments
        if region.startswith("/*", i):
            j = region.find("*/", i + 2)
            if j == -1:
                break
            i = j + 2
            continue

        parsed_if = _try_parse_if_at(i)
        if parsed_if is not None:
            cond, new_pos, is_else_if = parsed_if
            must_have, must_not_have = _parse_output_find_conditions(cond)

            base_depth = depth
            if is_else_if:
                # Implied negation of previous siblings in this chain.
                for sib_mh, _sib_mnh in chains.get(base_depth, []):
                    must_not_have |= set(sib_mh)
            else:
                # Start a new chain at this depth.
                chains[base_depth] = []

            block_depth = depth + 1
            cond_stack.append((block_depth, must_have, must_not_have))
            # Record this sibling condition for possible later else/else-if blocks.
            chains.setdefault(base_depth, []).append((set(must_have), set(must_not_have)))
            i = new_pos
            depth = block_depth
            continue

        parsed_else = _try_parse_else_block_at(i)
        if parsed_else is not None:
            base_depth = depth
            implied_not: set[str] = set()
            for sib_mh, _sib_mnh in chains.get(base_depth, []):
                implied_not |= set(sib_mh)

            block_depth = depth + 1
            if implied_not:
                cond_stack.append((block_depth, set(), implied_not))

            # Chain ends after else.
            chains.pop(base_depth, None)
            i = parsed_else
            depth = block_depth
            continue

        # Track braces
        ch = region[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            # Pop any condition blocks that ended
            while cond_stack and cond_stack[-1][0] > depth:
                cond_stack.pop()
            # Discard any chain state deeper than current depth
            for d in list(chains.keys()):
                if d > depth:
                    chains.pop(d, None)
            i += 1
            continue

        # Capture direct string literals and string concatenations with fondleTarget.
        if region.startswith("newShot.push_back", i):
            # Try direct string literal first
            m = re.match(
                r'newShot\.push_back\(\s*"(?P<s>(?:\\.|[^"\\])*)"\s*\)\s*;',
                region[i:],
            )
            if m:
                angle = _unescape_cpp_string(m.group("s"))
                must_have_all: set[str] = set()
                must_not_have_all: set[str] = set()
                for _bd, mh, mnh in cond_stack:
                    must_have_all |= mh
                    must_not_have_all |= mnh
                options.append(
                    CameraAngleOption(
                        text=angle,
                        must_have=tuple(sorted(must_have_all)),
                        must_not_have=tuple(sorted(must_not_have_all)),
                    )
                )
                i += m.end()
                continue
            
            # Try string concatenation with fondleTarget variable
            # Pattern: newShot.push_back("prefix" + fondleTarget + "suffix");
            m = re.match(
                r'newShot\.push_back\(\s*"(?P<prefix>(?:\\.|[^"\\])*)"\s*\+\s*fondleTarget\s*\+\s*"(?P<suffix>(?:\\.|[^"\\])*)"\s*\)\s*;',
                region[i:],
            )
            if m:
                prefix = _unescape_cpp_string(m.group("prefix"))
                suffix = _unescape_cpp_string(m.group("suffix"))
                must_have_all: set[str] = set()
                must_not_have_all: set[str] = set()
                for _bd, mh, mnh in cond_stack:
                    must_have_all |= mh
                    must_not_have_all |= mnh
                
                # Generate all variants with possible fondleTarget values extracted from C++
                for target in fondle_targets:
                    angle = prefix + target + suffix
                    options.append(
                        CameraAngleOption(
                            text=angle,
                            must_have=tuple(sorted(must_have_all)),
                            must_not_have=tuple(sorted(must_not_have_all)),
                        )
                    )
                i += m.end()
                continue

        i += 1

    if not options:
        raise ValueError(
            "getShot() contained no parseable camera angles (no direct newShot.push_back(\"...\") literals)"
        )

    return options


def load_camera_angles_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load camera angle options by parsing ai.cpp's getShot() newShot list.

    Note: use CAMERA_ANGLE_OPTIONS if you need the associated output.find(...) gating.
    """
    return [opt.text for opt in _load_camera_angle_options_from_cpp(cpp_path)]


def load_hair_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load HAIR by parsing ai.cpp's getHair() haircolor list."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    region = _extract_function_region(text, "getHair")

    # Extract the initializer list used for:
    #   std::string haircolor = pickRandomString({"...", ...});
    m2 = re.search(
        r"\bhaircolor\b\s*=\s*pickRandomString\s*\(\s*\{(?P<list>.*?)\}\s*\)\s*;",
        region,
        flags=re.DOTALL,
    )
    if not m2:
        raise ValueError("Could not find haircolor pickRandomString({..}) in getHair()")

    list_src = m2.group("list")
    raw = re.findall(r'"((?:\\.|[^"\\])*)"', list_src)
    hair = [_unescape_cpp_string(s).strip() for s in raw]

    if not hair:
        raise ValueError("getHair() haircolor list was empty")

    return hair


def load_style_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load STYLE by parsing ai.cpp's getHair() hairstyle options."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    region = _extract_function_region(text, "getHair")

    # Extract the initializer list used for:
    #   std::string hairstyle = pickRandomString({"...", ...});
    m2 = re.search(
        r"\bhairstyle\b\s*=\s*pickRandomString\s*\(\s*\{(?P<list>.*?)\}\s*\)\s*;",
        region,
        flags=re.DOTALL,
    )
    if not m2:
        raise ValueError("Could not find hairstyle pickRandomString({..}) in getHair()")

    list_src = m2.group("list")
    raw = re.findall(r'"((?:\\.|[^"\\])*)"', list_src)
    style = [_unescape_cpp_string(s).strip() for s in raw]
    if not style:
        raise ValueError("getHair() hairstyle list was empty")
    return style


def load_upper_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load UPPER clothing by parsing ai.cpp's pickUpper() clothing options."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")
    region = _extract_function_region(text, "pickUpper")

    # Find all pickRandomString({...}) calls in pickUpper
    upper_items = []
    for m in re.finditer(
        r"pickRandomString\s*\(\s*\{(?P<list>.*?)\}\s*\)",
        region,
        flags=re.DOTALL,
    ):
        list_src = m.group("list")
        # Only extract complete string literals, not fragments from concatenations
        # Look for strings that are NOT followed by + (which indicates concatenation)
        for line in list_src.split('\n'):
            # Match complete strings: "..." that are followed by comma or closing brace
            for item_match in re.finditer(r'"((?:\\.|[^"\\])*)"\s*(?:[,}])', line):
                unescaped = _unescape_cpp_string(item_match.group(1)).strip()
                # Skip empty strings and obvious fragments (ending with space suggests concatenation)
                if unescaped and not unescaped.endswith(' '):
                    upper_items.append(unescaped)

    if not upper_items:
        raise ValueError("pickUpper() contained no clothing options")

    return upper_items


def load_lower_from_cpp(cpp_path: Path | None = None) -> list[str]:
    """Load LOWER clothing by parsing ai.cpp's pickLower() clothing options."""
    if cpp_path is None:
        cpp_path = Path(__file__).with_name("ai.cpp")

    text = cpp_path.read_text(encoding="utf-8", errors="ignore")
    region = _extract_function_region(text, "pickLower")

    # Find all pickRandomString({...}) calls in pickLower
    lower_items = []
    for m in re.finditer(
        r"pickRandomString\s*\(\s*\{(?P<list>.*?)\}\s*\)",
        region,
        flags=re.DOTALL,
    ):
        list_src = m.group("list")
        # Only extract complete string literals, not fragments from concatenations
        for line in list_src.split('\n'):
            # Match complete strings: "..." that are followed by comma or closing brace
            for item_match in re.finditer(r'"((?:\\.|[^"\\])*)"\s*(?:[,}])', line):
                unescaped = _unescape_cpp_string(item_match.group(1)).strip()
                # Skip empty strings and obvious fragments (ending with space suggests concatenation)
                if unescaped and not unescaped.endswith(' '):
                    lower_items.append(unescaped)

    if not lower_items:
        raise ValueError("pickLower() contained no clothing options")

    return lower_items


COLORS = load_colors_from_cpp()

HAIR = load_hair_from_cpp()

STYLE = load_style_from_cpp()

MATERIAL = load_material_from_cpp()

MASKCOLOR = load_maskcolor_from_cpp()

MOUTHMASK_MATERIAL = load_mouthmask_material_from_cpp()

UPPER = load_upper_from_cpp()

LOWER = load_lower_from_cpp()


def _detect_body_focus_type(text: str) -> str:
    """Detect kBodyFocusType (UPPER, LOWER, or FULL) from text content.
    
    Based on body part mentions that are conditionally added in getBody():
    - UPPER indicators: arms, neck, jewelry (when LOWER parts absent)
    - LOWER indicators: thighs, calves, legs, feet, ass (when UPPER parts absent)
    - FULL: both present
    """
    text_lower = text.lower()
    
    # UPPER-specific indicators (from "if (kBodyFocusType != LOWER)" block)
    has_upper = any(indicator in text_lower for indicator in [
        'arms', 'neck', 'earring', 'bracelet', 'necklace', 'ring'
    ])
    
    # LOWER-specific indicators (from "if (kBodyFocusType != UPPER" block)
    has_lower = any(indicator in text_lower for indicator in [
        'thighs', 'calves', 'legs', 'feet', 'barefoot', 'ass'
    ])
    
    if has_upper and has_lower:
        return 'FULL'
    elif has_upper:
        return 'UPPER'
    elif has_lower:
        return 'LOWER'
    else:
        # Default to FULL if no clear indicators
        return 'FULL'


def _filter_fondle_targets_by_body_focus(targets: list[str], body_focus: str) -> list[str]:
    """Filter fondleTarget values based on kBodyFocusType.
    
    From ai.cpp:
        if (kBodyFocusType == UPPER)
            fondleTarget = "breasts";
        else if (kBodyFocusType == LOWER)
            fondleTarget = pickRandomString({"perfect small round ass", "thick thighs", "soles of feet"});
        else if (kBodyFocusType == FULL)
            fondleTarget = pickRandomString({"perfect breasts", "perfect small round ass", "thick thighs", "soles of feet"});
    """
    if body_focus == 'UPPER':
        return [t for t in targets if t == 'breasts']
    elif body_focus == 'LOWER':
        return [t for t in targets if t in ('perfect small round ass', 'thick thighs', 'soles of feet')]
    else:  # FULL
        return [t for t in targets if t in ('perfect breasts', 'perfect small round ass', 'thick thighs', 'soles of feet')]


CAMERA_ANGLE_OPTIONS = _load_camera_angle_options_from_cpp()
CAMERA_ANGLES = [opt.text for opt in CAMERA_ANGLE_OPTIONS]


def _camera_option_matches(text: str, opt: CameraAngleOption) -> bool:
    hay = text.lower()
    for s in opt.must_have:
        if s.lower() not in hay:
            return False
    for s in opt.must_not_have:
        if s.lower() in hay:
            return False
    return True

def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[0].isupper() and original[1:].islower():
        return replacement.capitalize()
    return replacement.lower()


def build_pattern(colors):
    # word-boundary match, case-insensitive
    # Important: ignore empty strings (C++ lists may include "" to mean "no material").
    esc = [re.escape(c) for c in colors if c]
    if not esc:
        # A regex that matches nothing.
        return re.compile(r"(?!x)x")
    return re.compile(r"\b(" + r"|".join(esc) + r")\b", re.IGNORECASE)


def convert_colors(text: str, rng: random.Random, colors=COLORS):
    pattern = build_pattern(colors)
    counts = Counter()
    hair_set = {h.lower() for h in HAIR}

    def repl(m):
        orig = m.group(0)
        key = orig.lower()

        # Avoid recoloring hair colors like "brown" in the phrase "brown hair".
        # These should be handled by convert_hair() instead.
        if key in hair_set:
            after = text[m.end():]
            if re.match(r"^\s+hair\b", after, flags=re.IGNORECASE):
                return orig

        # Special-case: Use maskcolor for mouth_mask.
        # Handles: "<color> mouth_mask" and "<color> <material> mouth_mask".
        after = text[m.end():]
        if re.match(r"^\s*(?:[a-z_]+\s+){0,2}mouth_mask\b", after, flags=re.IGNORECASE):
            choices = list(MASKCOLOR)
        else:
            choices = list(colors)

        # allow choosing the same value as the original (permit same-value replacements)
        if not choices:
            return orig
        new = rng.choice(choices)
        counts[key] += 1
        return preserve_case(orig, new)

    out = pattern.sub(repl, text)
    return out, counts


def _find_first_camera_angle(text: str, camera_angles: list[str]) -> tuple[str | None, int | None, int | None]:
    """Return (match_text, start, end) for the earliest camera angle occurrence.

    Also detects dynamic patterns like: (high angle shot:1.2)
    """
    if not text:
        return None, None, None

    best = (None, None, None)  # type: ignore[assignment]
    best_start: int | None = None

    # Prefer exact-string matches from the known angle list
    lower = text.lower()
    for a in camera_angles:
        if not a:
            continue
        idx = lower.find(a.lower())
        if idx == -1:
            continue
        if best_start is None or idx < best_start:
            best_start = idx
            best = (text[idx:idx + len(a)], idx, idx + len(a))

    # Handle dynamic C++ angle: (high angle shot:<float>)
    m = re.search(r"\(high angle shot\s*:\s*\d+(?:\.\d+)?\)", text, flags=re.IGNORECASE)
    if m:
        if best_start is None or m.start() < best_start:
            best = (text[m.start():m.end()], m.start(), m.end())

    return best  # type: ignore[return-value]


def convert_camera(
    text: str,
    rng: random.Random,
    camera_angles: list[str] = CAMERA_ANGLES,
    camera_options: list[CameraAngleOption] = CAMERA_ANGLE_OPTIONS,
) -> tuple[str, bool]:
    """Replace the first found camera angle with another one.

    Respects getShot(output) gating logic by filtering candidate angles to those whose
    output.find(...) conditions match the provided text. Also filters fondleTarget-based
    angles according to detected kBodyFocusType.
    """
    found, start, end = _find_first_camera_angle(text, camera_angles)
    if not found or start is None or end is None:
        return text, False

    # Detect body focus type from text content
    body_focus = _detect_body_focus_type(text)
    
    # Only choose among angles that would be eligible for this output, per C++ checks.
    eligible = []
    for opt in camera_options:
        if not _camera_option_matches(text, opt):
            continue
        
        # Additional filtering: if this angle contains a fondleTarget value,
        # check if it's valid for the detected body focus type
        angle_lower = opt.text.lower()
        contains_fondle_target = False
        for target in ['breasts', 'perfect breasts', 'perfect small round ass', 'thick thighs', 'soles of feet']:
            if target in angle_lower:
                contains_fondle_target = True
                # Filter based on body focus type
                valid_targets = _filter_fondle_targets_by_body_focus([target], body_focus)
                if not valid_targets:
                    # This angle uses a fondleTarget not valid for this body focus
                    break
        else:
            # Either doesn't contain fondleTarget, or all checks passed
            eligible.append(opt.text)
    
    # If no angles match the output conditions, fall back to all angles (ignore conditions).
    # This handles cases where a camera angle exists in the text but doesn't satisfy
    # its own output.find() conditions - we still want to allow randomization.
    if not eligible:
        eligible = camera_angles

    current_lower = found.lower()
    choices = [a for a in eligible if a.lower() != current_lower]
    if not choices:
        # Nothing else eligible; treat as no-op.
        return text, False

    replacement = rng.choice(choices)
    new_text = text[:start] + replacement + text[end:]
    return new_text, True

def convert_hair(text: str, rng: random.Random, hair=HAIR):
    pattern = build_pattern(hair)
    counts = Counter()

    def repl(m):
        orig = m.group(0)
        key = orig.lower()
        # Only replace hair colors when they are part of a "<color> hair" phrase.
        after = text[m.end():]
        if not re.match(r"^\s+hair\b", after, flags=re.IGNORECASE):
            return orig
        # allow choosing the same value as the original (permit same-value replacements)
        choices = list(hair)
        if not choices:
            return orig
        new = rng.choice(choices)
        counts[key] += 1
        return preserve_case(orig, new)

    out = pattern.sub(repl, text)
    return out, counts

def convert_material(text: str, rng: random.Random, material=MATERIAL):
    pattern = build_pattern(material)
    counts = Counter()

    def repl(m):
        orig = m.group(0)
        key = orig.lower()
        
        # Special-case: Use mouthMaskMaterial for mouth_mask.
        # Handles: "<color> <material> mouth_mask".
        after = text[m.end():]
        if re.match(r"^\s*mouth_mask\b", after, flags=re.IGNORECASE):
            choices = [mat for mat in MOUTHMASK_MATERIAL if mat]
        else:
            choices = [mat for mat in material if mat]
        
        # allow choosing the same value as the original (permit same-value replacements)
        if not choices:
            return orig
        new = rng.choice(choices)
        counts[key] += 1
        return preserve_case(orig, new)

    out = pattern.sub(repl, text)
    return out, counts

def convert_style(text: str, rng: random.Random, style=STYLE):
    pattern = build_pattern(style)
    counts = Counter()

    def repl(m):
        orig = m.group(0)
        key = orig.lower()
        # Only replace hairstyle phrases when they are part of a "hair <style>" phrase.
        # This prevents changing unrelated words like "up" in other contexts.
        before = text[max(0, m.start() - 25):m.start()]
        if not re.search(r"hair\s+$", before, flags=re.IGNORECASE):
            return orig
        # allow choosing the same value as the original (permit same-value replacements)
        choices = list(style)
        if not choices:
            return orig
        new = rng.choice(choices)
        counts[key] += 1
        return preserve_case(orig, new)

    out = pattern.sub(repl, text)
    return out, counts


def convert_clothes(text: str, rng: random.Random, upper=UPPER, lower=LOWER):
    """Replace upper and lower clothing items with randomized alternatives.
    
    Looks for patterns like:
    - "(woman is wearing <color> <material> <clothing>)"
    - "(sleeping woman is wearing <color> <material> <clothing>)"
    """
    counts = Counter()
    result = text
    
    # Build sets for faster lookups and deduplicate
    upper_set = set(item.lower() for item in upper)
    lower_set = set(item.lower() for item in lower)
    
    # Items only in upper/lower (not duplicates)
    upper_only = {item.lower(): item for item in upper if item.lower() not in lower_set}
    lower_only = {item.lower(): item for item in lower if item.lower() not in upper_set}
    both = upper_set & lower_set
    
    # Pattern to match clothing phrases - capture everything inside the parentheses
    # Matches: (sleeping woman is wearing <color> <material> <item>)
    # or: (woman is wearing <color> <material> <item>)
    clothing_pattern = re.compile(
        r'\(((?:sleeping\s+)?woman\s+is\s+wearing\s+[^)]+)\)',
        re.IGNORECASE
    )
    
    def replace_clothing_item(match_text: str) -> tuple[str, bool]:
        # Try to find the actual clothing item in the match text
        match_lower = match_text.lower()
        
        # First try items that are unique to upper
        for item_lower, item_orig in upper_only.items():
            if item_lower in match_lower:
                # Found upper-only item - replace with another upper item
                upper_choices = [item for item in upper if item.lower() != item_lower]
                if upper_choices:
                    new_item = rng.choice(upper_choices)
                    idx = match_lower.find(item_lower)
                    new_text = match_text[:idx] + new_item + match_text[idx + len(item_orig):]
                    return new_text, True
        
        # Then try items unique to lower
        for item_lower, item_orig in lower_only.items():
            if item_lower in match_lower:
                # Found lower-only item - replace with another lower item
                lower_choices = [item for item in lower if item.lower() != item_lower]
                if lower_choices:
                    new_item = rng.choice(lower_choices)
                    idx = match_lower.find(item_lower)
                    new_text = match_text[:idx] + new_item + match_text[idx + len(item_orig):]
                    return new_text, True
        
        # Handle duplicates - try to determine from context (this is a fallback)
        for item_lower in both:
            if item_lower in match_lower:
                # For duplicates, randomly pick upper or lower (50/50)
                if rng.random() < 0.5:
                    choices = [item for item in upper if item.lower() != item_lower]
                else:
                    choices = [item for item in lower if item.lower() != item_lower]
                
                if choices:
                    new_item = rng.choice(choices)
                    # Find the original item from either list
                    orig_item = next((item for item in upper + lower if item.lower() == item_lower), None)
                    if orig_item:
                        idx = match_lower.find(item_lower)
                        new_text = match_text[:idx] + new_item + match_text[idx + len(orig_item):]
                        return new_text, True
        
        return match_text, False
    
    def repl(m):
        orig = m.group(0)
        inner = m.group(1)
        
        new_inner, changed = replace_clothing_item(inner)
        if changed:
            counts['clothes'] += 1
            return f'({new_inner})'
        
        return orig
    
    result = clothing_pattern.sub(repl, result)
    return result, counts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Input text file")
    p.add_argument("-o","--output", help="Output file (omit for stdout)")
    p.add_argument("--inplace", action="store_true", help="Overwrite input file")
    p.add_argument("--seed", type=int, help="Random seed for reproducibility")
    args = p.parse_args()

    if args.inplace and args.output:
        p.error("--inplace and --output are mutually exclusive")

    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input file not found: {inp}")
        raise SystemExit(2)

    txt = inp.read_text(encoding="utf-8")
    newtxt, counts_colors = convert_colors(txt, rng)
    newertxt, counts_hair = convert_hair(newtxt, rng)
    newesttxt, counts_style = convert_style(newertxt, rng)
    newestesttxt, counts_material = convert_material(newesttxt, rng)

    # combine counts from both conversion passes
    counts = counts_colors + counts_hair + counts_style + counts_material

    if args.inplace:
        inp.write_text(newestesttxt, encoding="utf-8")
        outpath = inp
    elif args.output:
        outpath = Path(args.output)
        outpath.write_text(newestesttxt, encoding="utf-8")
    else:
        print(newertxt)
        outpath = None

    print("--- Replacement summary ---")
    total = sum(counts.values())
    print(f"Total replacements: {total}")
    for k, v in counts.most_common():
        print(f"{k}: {v}")
    if outpath:
        print(f"Wrote: {outpath}")


if __name__ == '__main__':
    main()
