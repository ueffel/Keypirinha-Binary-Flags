import keypirinha as kp
import keypirinha_util as kpu
import re
import traceback


class BinaryFlags(kp.Plugin):
    DEZ = re.compile(r"^\d+$")
    HEX = re.compile(r"^0x[0-9a-fA-F]+$")
    BIN = re.compile(r"^0b[01]+$")
    CONFIG_PREFIX = "flags/"
    CATEGORY_VALUE = kp.ItemCategory.USER_BASE + 1
    CATEGORY_SINGLE_FLAG = kp.ItemCategory.USER_BASE + 2
    TARGET_DEZ = "flagsD"
    TARGET_HEX = "flagsX"
    TARGET_BIN = "flagsB"
    TARGET_SUFFIX_TRUE = "_only_true"
    TARGET_SUFFIX_FALSE = "_only_false"
    TARGET_PREFIX_FLAG = "flag_"
    ACTION_COPY_DEZ = "copy_dez"
    ACTION_COPY_HEX = "copy_hex"
    ACTION_COPY_BIN = "copy_bin"
    ACTION_COPY_NAME = "copy_name"
    UNKNOWN_FLAG_LABEL = "???"

    def __init__(self):
        super().__init__()
        self._flag_types = {}
        self._default_icon = None

    def _read_config(self):
        settings = self.load_settings()

        self._debug = settings.get_bool("debug", "main", False)

        for section in settings.sections():
            try:
                if section.startswith(self.CONFIG_PREFIX):
                    flag_type = {}
                    for key in settings.keys(section):
                        key_num = None
                        if self.DEZ.match(key):
                            key_num = int(key)
                        elif self.HEX.match(key):
                            key_num = int(key, 16)
                        elif self.BIN.match(key):
                            key_num = int(key, 2)

                        if key_num:
                            flag_type[key_num] = settings.get_stripped(key, section, "")
                        else:
                            self.warn(key, " could not be interpreted as number")
                    self._flag_types[section[len(self.CONFIG_PREFIX):]] = flag_type
            except Exception:
                self.err("Error while reading config section '{}':\n{}".format(section, traceback.format_exc()))

    def on_start(self):
        self._read_config()
        self._default_icon = self.load_icon("res://{}/binary-code-256.ico".format(self.package_full_name()))
        self.set_default_icon(self._default_icon)

        actions = [self.create_action(
            name=self.ACTION_COPY_DEZ,
            label="Copy flag as decimal number",
            short_desc="Copy to clipboard"
        ), self.create_action(
            name=self.ACTION_COPY_HEX,
            label="Copy flag as hexadecimal number",
            short_desc="Copy to clipboard"
        ), self.create_action(
            name=self.ACTION_COPY_BIN,
            label="Copy flag as binary number",
            short_desc="Copy to clipboard"
        ), self.create_action(
            name=self.ACTION_COPY_NAME,
            label="Copy name of flag",
            short_desc="Copy to clipboard"
        )]

        self.set_actions(self.CATEGORY_SINGLE_FLAG, actions)

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()

    def on_catalog(self):
        self.set_catalog([self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label="Binary Flags:",
            short_desc="Disassembles a value into binary flags",
            target="flags",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS
        )])

    def on_suggest(self, user_input, items_chain):
        if not items_chain:
            return

        items = []
        if len(items_chain) == 1:
            for flag_type in self._flag_types.keys():
                items.append(self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=flag_type,
                    short_desc=flag_type,
                    target=flag_type,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    loop_on_suggest=True
                ))

            self.set_suggestions(items, kp.Match.FUZZY, kp.Sort.SCORE_DESC)
        elif len(items_chain) >= 2:
            flag_type = self._flag_types[items_chain[1].target()]
            data_bag = items_chain[-1].data_bag()
            self.dbg("data_bag:", data_bag)

            if not user_input and data_bag:
                user_input = data_bag

            value = sum(flag_type.keys())
            show_dez = True
            show_hex = True
            show_bin = True

            if self.DEZ.match(user_input):
                value = int(user_input)
                show_dez = False
                show_hex = True
                show_bin = True
            elif self.HEX.match(user_input):
                value = int(user_input, 16)
                show_dez = True
                show_hex = False
                show_bin = True
            elif self.BIN.match(user_input):
                value = int(user_input, 2)
                show_dez = True
                show_hex = True
                show_bin = False
            elif user_input:
                value = 0
                show_dez = False
                show_hex = False
                show_bin = False

            if show_dez:
                items.append(self.create_item(
                        category=self.CATEGORY_VALUE,
                        label="{:d}".format(value),
                        short_desc="Dez",
                        target=self.TARGET_DEZ,
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE
                    ))
            if show_hex:
                items.append(self.create_item(
                        category=self.CATEGORY_VALUE,
                        label="{:X}".format(value),
                        short_desc="Hex",
                        target=self.TARGET_HEX,
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE
                    ))
            if show_bin:
                items.append(self.create_item(
                        category=self.CATEGORY_VALUE,
                        label="{:b}".format(value),
                        short_desc="Binary",
                        target=self.TARGET_BIN,
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE
                    ))

            show_only_true = items_chain[-1].target().endswith(self.TARGET_SUFFIX_TRUE)
            show_only_false = items_chain[-1].target().endswith(self.TARGET_SUFFIX_FALSE)
            show_all = items_chain[-1].target() == items_chain[1].target()

            if not show_only_true:
                item = self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Show only True flags",
                    short_desc="Show only flags, that are set within the value",
                    target=items_chain[1].target() + self.TARGET_SUFFIX_TRUE,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    loop_on_suggest=True
                )
                item.set_data_bag(user_input)
                items.append(item)
            if not show_only_false:
                item = self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Show only False flags",
                    short_desc="Show only flags, that are not set within the value",
                    target=items_chain[1].target() + self.TARGET_SUFFIX_FALSE,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    loop_on_suggest=True
                )
                item.set_data_bag(user_input)
                items.append(item)
            if not show_all:
                item = items_chain[1].clone()
                item.set_label("Show both (True and False) flags")
                item.set_short_desc("Show all flags, set or not set")
                item.set_data_bag(user_input)
                items.append(item)

            flag = 1
            biggest_flag = max(flag_type.keys())
            binary_digits = max(biggest_flag.bit_length(), value.bit_length())
            format_str = "{:0{bit_length}b}: {}"

            while flag <= value or flag <= biggest_flag:
                flag_set = flag & value == flag
                if (show_only_false and not flag_set) or (show_only_true and flag_set) or show_all:
                    if flag in flag_type:
                        items.append(self.create_item(
                            category=self.CATEGORY_SINGLE_FLAG,
                            label=str(flag_set).lower()
                            if show_all else format_str.format(flag, flag_type[flag], bit_length=binary_digits),
                            short_desc=format_str.format(flag, flag_type[flag], bit_length=binary_digits)
                            if show_all else "",
                            target=self.TARGET_PREFIX_FLAG + str(flag),
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=items_chain[1].target()
                        ))
                    else:
                        items.append(self.create_item(
                            category=self.CATEGORY_SINGLE_FLAG,
                            label=str(flag_set).lower()
                            if show_all else format_str.format(flag, self.UNKNOWN_FLAG_LABEL, bit_length=binary_digits),
                            short_desc=format_str.format(flag, self.UNKNOWN_FLAG_LABEL, bit_length=binary_digits)
                            if show_all else "",
                            target=self.TARGET_PREFIX_FLAG + str(flag),
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=items_chain[1].target()
                        ))
                flag <<= 1

            self.set_suggestions(items, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        self.dbg("On_execute")
        text = None
        if item.category() == self.CATEGORY_VALUE:
            text = item.label()
        elif item.category() == self.CATEGORY_SINGLE_FLAG:
            flag_value = int(item.target()[len(self.TARGET_PREFIX_FLAG):])
            self.dbg("Flag_value:", flag_value)
            flag_type = item.data_bag()
            self.dbg("Data_bag:", flag_type)

            if action is None or action.name() == self.ACTION_COPY_BIN:
                text = "{:b}".format(flag_value)
            elif action.name() == self.ACTION_COPY_DEZ:
                text = str(flag_value)
            elif action.name() == self.ACTION_COPY_HEX:
                text = "{:X}".format(flag_value)
            elif action.name() == self.ACTION_COPY_NAME:
                flags = self._flag_types[flag_type]
                if flag_value in flags:
                    text = flags[flag_value]
                else:
                    text = self.UNKNOWN_FLAG_LABEL

        self.dbg("Clipboard text:", text)
        if text:
            kpu.set_clipboard(text)
