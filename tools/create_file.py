# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

with open("big_test.bin", "wb") as f:
    f.seek(500 * 1024 * 1024 - 1)
    f.write(b"\0")
