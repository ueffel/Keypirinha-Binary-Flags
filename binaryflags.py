import keypirinha as kp
import keypirinha_util as kpu
import re
import traceback
import copy


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
                    data_bag=repr(FlagMeta(flag_type)),
                    loop_on_suggest=True
                ))

            self.set_suggestions(items, kp.Match.FUZZY, kp.Sort.SCORE_DESC)
        elif len(items_chain) >= 2:
            flag_meta = eval(items_chain[-1].data_bag())
            flag_type = self._flag_types[flag_meta.flag_type]

            if not user_input and flag_meta.value >= 0:
                user_input = str(flag_meta.value)

            if self.DEZ.match(user_input):
                value = int(user_input)
            elif self.HEX.match(user_input):
                value = int(user_input, 16)
            elif self.BIN.match(user_input):
                value = int(user_input, 2)
            else:
                value = sum(flag_type.keys())

            flag_meta.value = value
            self.dbg(flag_meta)

            dez_meta = copy.deepcopy(flag_meta)
            dez_meta.base = 10
            items.append(self.create_item(
                category=self.CATEGORY_VALUE,
                label="{:d}".format(value),
                short_desc="Dez   (press tab to show flags in dez, enter to copy)",
                target=self.TARGET_DEZ,
                args_hint=kp.ItemArgsHint.ACCEPTED,
                hit_hint=kp.ItemHitHint.IGNORE,
                data_bag=repr(dez_meta),
                loop_on_suggest=True
            ))
            hex_meta = copy.deepcopy(flag_meta)
            hex_meta.base = 16
            items.append(self.create_item(
                category=self.CATEGORY_VALUE,
                label="{:X}".format(value),
                short_desc="Hex   (press tab to show flags in hex, enter to copy)",
                target=self.TARGET_HEX,
                args_hint=kp.ItemArgsHint.ACCEPTED,
                hit_hint=kp.ItemHitHint.IGNORE,
                data_bag=repr(hex_meta),
                loop_on_suggest=True
            ))
            bin_meta = copy.deepcopy(flag_meta)
            bin_meta.base = 2
            items.append(self.create_item(
                category=self.CATEGORY_VALUE,
                label="{:b}".format(value),
                short_desc="Binary   (press tab to show flags in binary, enter to copy)",
                target=self.TARGET_BIN,
                args_hint=kp.ItemArgsHint.ACCEPTED,
                hit_hint=kp.ItemHitHint.IGNORE,
                data_bag=repr(bin_meta),
                loop_on_suggest=True
            ))

            show_only_true = flag_meta.show == self.TARGET_SUFFIX_TRUE
            show_only_false = flag_meta.show == self.TARGET_SUFFIX_FALSE
            show_all = not flag_meta.show

            if not show_only_true:
                only_true_meta = copy.deepcopy(flag_meta)
                only_true_meta.show = self.TARGET_SUFFIX_TRUE
                item = self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Show only True flags",
                    short_desc="Show only flags, that are set within the value",
                    target=items_chain[1].target() + self.TARGET_SUFFIX_TRUE,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=repr(only_true_meta),
                    loop_on_suggest=True
                )
                items.append(item)
            if not show_only_false:
                only_false_meta = copy.deepcopy(flag_meta)
                only_false_meta.show = self.TARGET_SUFFIX_FALSE
                item = self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Show only False flags",
                    short_desc="Show only flags, that are not set within the value",
                    target=items_chain[1].target() + self.TARGET_SUFFIX_FALSE,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=repr(only_false_meta),
                    loop_on_suggest=True
                )
                items.append(item)
            if not show_all:
                show_all_meta = copy.deepcopy(flag_meta)
                show_all_meta.show = ""
                item = self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Show both (True and False) flags",
                    short_desc="Show both (True and False) flags",
                    target=items_chain[1].target(),
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=repr(show_all_meta),
                    loop_on_suggest=True
                )
                items.append(item)

            flag = 1
            biggest_flag = max(flag_type.keys())
            binary_digits = max(biggest_flag.bit_length(), value.bit_length())
            hex_digits = int(binary_digits / 4)
            dez_digits = len(str(biggest_flag))

            if flag_meta.base == 2:
                format_str = "0b{:0{bit_length}b}: {}"
            elif flag_meta.base == 16:
                format_str = "0x{:0{hex_length}x}: {}"
            else:
                format_str = "{:0{length}}: {}"

            self.dbg("format:", format_str)

            while flag <= value or flag <= biggest_flag:
                flag_set = flag & value == flag
                if (show_only_false and not flag_set) or (show_only_true and flag_set) or show_all:
                    new_flag_meta = copy.deepcopy(flag_meta)
                    new_flag_meta.value = value | flag if not flag else value ^ flag
                    if flag in flag_type:
                        items.append(self.create_item(
                            category=self.CATEGORY_SINGLE_FLAG,
                            label=str(flag_set).lower()
                            if show_all else format_str.format(flag,
                                                               flag_type[flag],
                                                               bit_length=binary_digits,
                                                               hex_length=hex_digits,
                                                               length=dez_digits),
                            short_desc=(format_str.format(flag,
                                                          flag_type[flag],
                                                          bit_length=binary_digits,
                                                          hex_length=hex_digits,
                                                          length=dez_digits)
                                        if show_all else "")
                            + "   (press tab to toggle, enter to copy)",
                            target=self.TARGET_PREFIX_FLAG + str(flag),
                            args_hint=kp.ItemArgsHint.ACCEPTED,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=repr(new_flag_meta),
                            loop_on_suggest=True
                        ))
                    else:
                        items.append(self.create_item(
                            category=self.CATEGORY_SINGLE_FLAG,
                            label=str(flag_set).lower()
                            if show_all else format_str.format(flag,
                                                               self.UNKNOWN_FLAG_LABEL,
                                                               bit_length=binary_digits,
                                                               hex_length=hex_digits,
                                                               length=dez_digits),
                            short_desc=(format_str.format(flag,
                                                          self.UNKNOWN_FLAG_LABEL,
                                                          bit_length=binary_digits,
                                                          hex_length=hex_digits,
                                                          length=dez_digits)
                                        if show_all else "")
                            + "   (press tab to toggle, enter to copy)",
                            target=self.TARGET_PREFIX_FLAG + str(flag),
                            args_hint=kp.ItemArgsHint.ACCEPTED,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=repr(new_flag_meta),
                            loop_on_suggest=True
                        ))
                flag <<= 1

            self.set_suggestions(items, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        self.dbg("on_execute")
        text = None
        flag_meta = eval(item.data_bag())
        self.dbg(flag_meta)
        if item.category() == self.CATEGORY_VALUE:
            if flag_meta.base == 2:
                text = "{:b}".format(flag_meta.value)
            elif flag_meta.base == 10:
                text = str(flag_meta.value)
            elif flag_meta.base == 16:
                text = "{:X}".format(flag_meta.value)
        elif item.category() == self.CATEGORY_SINGLE_FLAG:
            flag_value = int(item.target()[len(self.TARGET_PREFIX_FLAG):])
            flag_type = self._flag_types[flag_meta.flag_type]
            if flag_meta.base == 2:
                text = "0b{:b} {}".format(flag_value,
                                          flag_type[flag_value] if flag_value in flag_type else self.UNKNOWN_FLAG_LABEL)
            elif flag_meta.base == 10:
                text = "{} {}".format(flag_value,
                                      flag_type[flag_value] if flag_value in flag_type else self.UNKNOWN_FLAG_LABEL)
            elif flag_meta.base == 16:
                text = "0x{:X} {}".format(flag_value,
                                          flag_type[flag_value] if flag_value in flag_type else self.UNKNOWN_FLAG_LABEL)

        self.dbg("Clipboard text:", text)
        if text:
            kpu.set_clipboard(text)


class FlagMeta(object):
    __slots__ = ("flag_type", "value", "show", "base")

    def __init__(self, flag_type, value=-1, show="", base=2):
        self.flag_type = flag_type
        self.value = value
        self.show = show
        self.base = base

    def __str__(self):
        return "{} {} {} {}".format(self.flag_type, self.value, self.show, self.base)

    def __repr__(self):
        return "FlagMeta(flag_type={}, value={}, show={}, base={})" \
            .format(repr(self.flag_type),
                    repr(self.value),
                    repr(self.show),
                    repr(self.base))
