import copy

import enum
from furrifier_utils_basics import is_any_part_installed
from furrifier_utils_enums import FurryTag
from furrifier_utils_notifier import show_notification


class TagOp(enum.Int):
    OR = 1
    AND = 2
    NOT = 3
    VAL = 4


def split_block(block: str):
    # If parenthesis is opened at start and not closed until group of parens at end, remove outer layer
    if block.startswith('(') and block.endswith(')'):
        starting_parens = 0
        inner_paren_level = 0
        counted_start = False
        temp_block = block.rstrip(')')
        for character in temp_block:
            if character == '(':
                if not counted_start:
                    starting_parens += 1
                else:
                    inner_paren_level += 1
            elif character == ')':
                if inner_paren_level > 0:
                    inner_paren_level -= 1
                else:
                    starting_parens -= 1
            else:
                counted_start = True

        if starting_parens:
            block = block[starting_parens:-starting_parens]

    # Actually do splitting
    sections = []
    cur_section = ""
    paren_level = 0
    quotes = False

    for character in block:
        # Open/Close parentheses
        if character == '(':
            if paren_level != 0:
                cur_section += character
            paren_level += 1
        elif character == ')':
            paren_level -= 1
            if paren_level != 0:
                cur_section += character
            if paren_level < 0:
                raise ValueError("Closed parentheses that weren't opened!")
        # Handle ref tags
        elif character == "'":
            quotes = not quotes
            cur_section += character
        # Split on spaces if not in parentheses or ref
        elif character == " ":
            if paren_level == 0 and not quotes:
                sections.append(cur_section)
                cur_section = ""
            else:
                cur_section += character
        # Just add other characters
        else:
            cur_section += character

    if cur_section != "":
        sections.append(cur_section)

    if paren_level != 0:
        raise ValueError("Opened parentheses weren't closed!")

    return sections


class FurryTagCondition:
    all_parts = {}
    all_species = {}
    custom_tags = {}
    custom_tag_num = 1000
    max_recursion = 50

    def __init__(self, block: str, recursion_check=0):
        self.recursion_level = recursion_check
        self.left = None
        self.right = None
        self.operation = None

        # Recursion check
        if recursion_check > FurryTagCondition.max_recursion:
            raise RecursionError("Infinite Tags detected, probably due to circular reference")

        self.evaluate_block(block)

        # If two identical conditions, the second will never matter
        if self.left == self.right:
            self.right = None
            self.operation = TagOp.VAL

        # If only one condition, and it's a FurryTagCondition, copy it up to this one
        if self.operation == TagOp.VAL:
            if self.left is None and isinstance(self.right, FurryTagCondition):
                self.operation = self.right.operation
                self.left = self.right.left
                self.right = self.right.right
            elif self.right is None and isinstance(self.left, FurryTagCondition):
                self.operation = self.left.operation
                self.right = self.left.right
                self.left = self.left.left

    def __eq__(self, other):
        if isinstance(other, FurryTagCondition):
            return self.left == other.left and self.right == other.right and self.operation == other.operation
        return False

    def __str__(self):
        if self.operation == TagOp.OR:
            return f"({self.left} | {self.right})"
        elif self.operation == TagOp.AND:
            return f"({self.left} & {self.right})"
        elif self.operation == TagOp.NOT:
            return f"(NOT {self.right})"
        elif self.operation == TagOp.VAL:
            return f"{self.left}"
        else:
            return f"Invalid operation: {self.operation}"

    def __hash__(self):
        return hash(str(self))

    def passes(self, tags: [FurryTag]) -> bool:
        if self.operation == TagOp.OR:
            return self.left.passes(tags) or self.right.passes(tags)
        elif self.operation == TagOp.AND:
            return self.left.passes(tags) and self.right.passes(tags)
        elif self.operation == TagOp.NOT:
            return not self.right.passes(tags)
        elif self.operation == TagOp.VAL:
            return self.left in tags
        else:
            raise ValueError(f"Invalid operation: {self.operation}")

    def evaluate_block(self, block: str):
        # If blank, it's valid
        if not block:
            self.operation = TagOp.VAL
            self.left = FurryTag.MISC_VALID
            return

        # Evaluate OR before AND, due to recursion the AND will take precedence, also do last to first
        try:
            block_segments = split_block(block)

            # Evaluate ORs
            for i in reversed(range(len(block_segments))):
                if block_segments[i].casefold() == "OR".casefold() or block_segments[i] == "|":
                    self.operation = TagOp.OR
                    self.left, self.right = self.evaluate_sides(block_segments, i, block_segments[i])

                    # If operating with values of VALID or INVALID, do pre-shortcutting
                    if self.left.is_valid() or self.right.is_valid():
                        # If either valid, condition is always valid
                        self.operation = TagOp.VAL
                        self.left = FurryTag.MISC_VALID
                        self.right = None
                    # If either invalid, that one doesn't matter
                    elif self.left.is_invalid():
                        self.operation = TagOp.VAL
                        self.left = self.right
                        self.right = None
                    elif self.right.is_invalid():
                        self.operation = TagOp.VAL
                        self.right = None
                    return
            # Evaluate ANDs
            for i in reversed(range(len(block_segments))):
                if block_segments[i].casefold() == "AND".casefold() or block_segments[i] == "&":
                    self.operation = TagOp.AND
                    self.left, self.right = self.evaluate_sides(block_segments, i, block_segments[i])

                    # If operating with values of VALID or INVALID, do pre-shortcutting
                    if self.left.is_invalid() or self.right.is_invalid():
                        # If either invalid, condition is always invalid
                        self.operation = TagOp.VAL
                        self.left = FurryTag.MISC_INVALID
                        self.right = None
                    # If either is valid, that one doesn't matter
                    elif self.left.is_valid():
                        self.operation = TagOp.VAL
                        self.left = self.right
                        self.right = None
                    elif self.right.is_valid():
                        self.operation = TagOp.VAL
                        self.right = None
                    return
            # Evaluate NOTs
            for i in reversed(range(len(block_segments))):
                if block_segments[i].casefold() == "NOT".casefold() or block_segments[i] == "!":
                    if i == len(block_segments):
                        raise IndexError(f"Cannot evaluate NOT without a condition on its right!")
                    self.operation = TagOp.NOT
                    self.right = FurryTagCondition(" ".join(block_segments[i + 1:]), self.recursion_level+1)

                    # If NOTing valid or invalid, shortcut to new value
                    if self.right.is_valid():
                        self.operation = TagOp.VAL
                        self.left = FurryTag.MISC_INVALID
                        self.right = None
                    elif self.right.is_invalid():
                        self.operation = TagOp.VAL
                        self.left = FurryTag.MISC_VALID
                        self.right = None

                    return

            self.operation = TagOp.VAL
            # If we are at this point, there should only be one value in the tag
            if len(block_segments) != 1:
                raise ValueError(f"Multiple conditions with no comparisons found, is a space or operator missing?")
            condition = block_segments[0]

            # Evaluate reference tags
            if condition.startswith("P'"):
                part_ref = condition[2:-1]
                if part_ref in FurryTagCondition.all_parts:
                    reffed_part = FurryTagCondition.all_parts[part_ref]

                    # Substitute Parts:
                    if 'part_options' in reffed_part:
                        if is_any_part_installed(list(reffed_part['part_options'].values())):
                            if 'requires' in reffed_part:
                                self.left = FurryTagCondition(reffed_part['requires'], self.recursion_level+1)
                            else:
                                self.left = FurryTag.MISC_VALID
                        else:
                            self.left = FurryTag.MISC_INVALID
                    elif 'ids' not in reffed_part or is_any_part_installed(reffed_part['ids']):
                        if 'requires' in reffed_part:
                            self.left = FurryTagCondition(reffed_part['requires'], self.recursion_level+1)
                        else:
                            self.left = FurryTag.MISC_VALID
                    else:
                        self.left = FurryTag.MISC_INVALID
                else:
                    raise ValueError(f"Unrecognized referenced part: {part_ref}")
            elif condition.startswith("S'"):
                species_ref = condition[2:-1]
                if species_ref in FurryTagCondition.all_species:
                    reffed_species = FurryTagCondition.all_species[species_ref]
                    if 'requires' in reffed_species:
                        self.left = FurryTagCondition(reffed_species['requires'])
                    else:
                        self.left = FurryTag.MISC_VALID
                else:
                    raise ValueError(f"Unrecognized referenced species: {species_ref}")
            elif condition.casefold() in FurryTagCondition.custom_tags:
                self.left = FurryTagCondition.custom_tags[condition.casefold()]
            elif condition.upper() in FurryTag:
                self.left = FurryTag[condition.upper()].value
            elif condition[0] == '(' and condition[-1] == ')':
                self.evaluate_block(condition[1:-1])
            else:
                raise ValueError(f"Unrecognized tag: {condition}")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Cannot evaluate '{block}': {e}")

    def evaluate_sides(self, segments: [str], index: int, operation: str):
        if index == 0 or index == len(segments):
            raise IndexError(f"Cannot evaluate {operation} without a condition on both sides")

        left = FurryTagCondition(" ".join(segments[:index]), self.recursion_level+1)
        right = FurryTagCondition(" ".join(segments[index + 1:]), self.recursion_level+1)
        return left, right

    def is_valid(self) -> bool:
        return self.operation == TagOp.VAL and self.left == FurryTag.MISC_VALID

    def is_invalid(self) -> bool:
        return self.operation == TagOp.VAL and self.left == FurryTag.MISC_INVALID

    def is_pref_based(self) -> bool:
        if self.operation == TagOp.VAL:
            return self.left < 100
        elif self.operation in (TagOp.OR, TagOp.AND):
            return self.left.is_pref_based() or self.right.is_pref_based()
        elif self.operation == TagOp.NOT:
            return self.right.is_pref_based()
        else:
            raise ValueError(f"Invalid operation: {self.operation}")


def check_custom_tags(custom_tag_labels: [str]):
    """
    Checks all the custom tags and assigns them numbers

    Args:
        custom_tag_labels (list of str): The list of custom tags to register

    Returns:
        dict: The dict of custom tags and their assigned numbers
    """
    for custom_tag in custom_tag_labels:
        FurryTagCondition.custom_tags[custom_tag.casefold()] = FurryTagCondition.custom_tag_num
        FurryTagCondition.custom_tag_num += 1


def stringify_conditions(data: dict) -> dict:
    new_data = {}
    for key, value in data.items():
        if isinstance(key, FurryTagCondition):
            new_key = str(key)
        else:
            new_key = key

        if isinstance(value, dict):
            new_value = stringify_conditions(value)
        elif isinstance(value, FurryTagCondition):
            new_value = str(value)
        else:
            new_value = value

        new_data[new_key] = new_value

    return new_data
