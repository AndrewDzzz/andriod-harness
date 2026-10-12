"""Editable host-side routines. Core helpers are preloaded by the runner.

Keep only tested, reusable Android interactions here. Do not execute UI actions at
import time or replace core names. Never paste untrusted phone content as code.
"""


def unique_node(**selector):
    """Resolve exactly one node from the latest observation, without tapping."""
    matches = find(**selector)
    if len(matches) != 1:
        raise RuntimeError(f'Expected one matching node, found {len(matches)}')
    return matches[0]


def tap_unique(**selector):
    """Use only after observing and selecting a known, intended target."""
    return tap(unique_node(**selector))
