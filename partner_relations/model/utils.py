# -*- coding: utf-8 -*-
"""Utility functions for *_all Abstract models which have two records
for each normal record: one direct and one inverse
"""

PADDING = 2


def ids_with_inverse(direct_ids, inverse_ids):
    """Map abstract inversable types to ids of partner realtion types

    Use a padding of 2:
      * even numbers are the direct relationships
      * odd numbers are the inverse relationships
    """
    return ids_to_direct(direct_ids), ids_to_inverse(inverse_ids)


def both_to_ids(ids):
    """Unmap relation types back to relation type ids

    Use a padding of 2:
      * odd numbers are the direct relationships
      * even numbers are the inverse relationships
    Remove duplicates
    """
    return list(set(map(both_to_id, ids)))


def both_to_id(res_id):
    """Unmap relation types back to relation type ids

    Use a padding of 2:
      * odd numbers are the direct relationships
      * even numbers are the inverse relationships
    Remove duplicates
    """
    return (get_id(res_id) - 1) / PADDING + 1


def ids_to_direct(direct_ids):
    """Get abstract ids of direct relationship from relationship type
    :param direct_ids: Ids of a relationship type
    :type direct_ids: list or browse_record list
    :return: List of Abstract id of direct relationship
    :rtype: list
    """
    return map(id_to_direct, direct_ids)


def id_to_direct(direct_id):
    """Get abstract id of direct relationship from relationship type
    :param direct_id: Id of a relationship type
    :type direct_id: int or long
    :return: Abstract id of direct relationship
    :rtype: int or long
    """
    return get_id(direct_id) * PADDING - 1


def ids_to_inverse(inverse_ids):
    """Get abstract ids of inverse relationship from relationship type
    :param inverse_ids: Ids of a relationship type
    :type inverse_ids: list or browse_record list
    :return: List of Abstract id of inverse relationship
    :rtype: list
    """
    return map(id_to_inverse, inverse_ids)


def id_to_inverse(inverse_id):
    """Get abstract id of inverse relationship from relationship type
    :param inverse_id: Id of a relationship type
    :type inverse_id: int or long
    :return: Abstract id of inverse relationship
    :rtype: int or long
    """
    return get_id(inverse_id) * PADDING


def id_is_direct(res_id):
    """Identify if this object's id refers to a direct or inverse relation
    :param res_id: Id of a relationship type
    :type res_id: int or long
    :return: If the relation is direct or inverse
    :rtype: bool
    """
    return bool(get_id(res_id) % PADDING)


def get_id(res_id):
    """Return id from browse object or id

    :param res_id: Object to get id from
    :type res_id: int, long or browse_record
    :return: id of browse_record
    :rtype: int or long
    """
    if isinstance(res_id, (int, long)):
        res_id = res_id
    else:
        res_id = res_id.id
    return res_id
