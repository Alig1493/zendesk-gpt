from typing import List

from langchain.chains.query_constructor.schema import AttributeInfo

DOCUMENT_CONTENT_DESCRIPTION = "Collection of Zendesk tickets in JSON"
METADATA_DESCRIPTION_DICT = {
    "assignee_id": "assignee id in integer of the zendesk ticket",
    "brand_id": "brand id in integer of the zendesk ticket",
    "collaborator_ids": "List of collaborator id's of the zendesk ticket",
    "created_at": "creation date time of the zendesk ticket",
    "custom_fields": "list of custom fields of the zendesk ticket",
    "description": "description of the zendesk ticket",
    "due_at": "due at datetime for the zendesk ticket",
    "external_id": "external id of the zendesk ticket",
    "fields": "list of fields of the zendesk ticket",
    "forum_topic_id": "forum topic id of the zendesk ticket",
    "group_id": "group id  in integer of the zendesk ticket",
    "has_incidents": "boolean field to indicate if zendesk ticket has incidents",
    "id": "zendesk ticket id in integer",
    "organization_id": "organization id in integer of the zendesk ticket",
    "priority": "priority rating of the zendesk ticket",
    "problem_id": "problem id in integer of the zendesk ticket",
    "raw_subject": "raw subject of the zendesk ticket",
    "recipient": "email address of the recipient of the zendesk ticket",
    "requester_id": "requester id in integer of the zendesk ticket",
    "satisfaction_rating": "satisfaction rating of the zendesk ticket",
    "sharing_agreement_ids": "sharing agreement ids of the zendesk ticket",
    "status": "status of the zendesk ticket",
    "subject": "subject of zendesk ticket",
    "submitter_id": "submitter id in integer of the zendesk ticket",
    "tags": "list of tags of the zendesk ticket",
    "type": "type of zendesk ticket",
    "updated_at": "updated at datetime of zendesk ticket",
    "url": "url of the zendesk ticket",
    "follower_ids": "follower_ids of the zendesk ticket",
    "email_cc_ids": "email_cc_ids of the zendesk ticket",
    "is_public": "boolean field denoting in zendesk ticket is public or not",
    "custom_status_id": "custom status id of the zendesk ticket",
    "followup_ids": "list of followup_ids of the zendesk ticket",
    "allow_channelback": "boolean field denoting if channelback is allowed for zendesk ticket",
    "allow_attachments": "boolean field denoting if attachments is allowed for zendesk ticket",
    "from_messaging_channel": "boolean field denoting if zendesk ticket was from messaging channel",
    "via": "extra dict information for zendesk ticket",
}


def create_metadata_field_info(json_dict_list) -> List[AttributeInfo]:
    metadata_field_info = []
    for json_dict_key, json_dict_value in json_dict_list[0].items():
        metadata_field_info.append(
            AttributeInfo(
                **{
                    "name": json_dict_key,
                    "description": METADATA_DESCRIPTION_DICT[json_dict_key],
                    "type": "integer" if isinstance(json_dict_value, int) else "string",
                }
            )
        )
    return metadata_field_info
