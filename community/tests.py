from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from community.models import CommunityGroup, GroupMembership, Challenge, ChallengeParticipant
from community.models import CommunityPost, CommunityPostReaction, CommunityPostComment, GroupChatMessage
from community.models import (
	CommunityNotification,
	UserCommunityPreference,
	GroupChatReadState,
	UserBadge,
)
from steps.models import DailyStepLog


class CommunityJoinGroupTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='member@example.com', password='testpass123')
		self.owner = User.objects.create_user(email='owner@example.com', password='testpass123')
		self.client.force_authenticate(user=self.user)

	def test_join_public_group_by_group_id(self):
		group = CommunityGroup.objects.create(
			name='Morning Walkers',
			created_by=self.owner,
			is_public=True,
		)

		response = self.client.post(
			'/api/v1/community/groups/join/',
			{'group_id': str(group.id)},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(
			GroupMembership.objects.filter(user=self.user, group=group, is_active=True).exists()
		)

	def test_private_group_rejects_group_id_join(self):
		group = CommunityGroup.objects.create(
			name='Private Squad',
			created_by=self.owner,
			is_public=False,
		)

		response = self.client.post(
			'/api/v1/community/groups/join/',
			{'group_id': str(group.id)},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('group_id', response.data)

	def test_join_private_group_by_invite_code(self):
		group = CommunityGroup.objects.create(
			name='Invite Only',
			created_by=self.owner,
			is_public=False,
		)

		response = self.client.post(
			'/api/v1/community/groups/join/',
			{'invite_code': group.invite_code},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(
			GroupMembership.objects.filter(user=self.user, group=group, is_active=True).exists()
		)


class CommunityChallengeCompatibilityTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='challenge@example.com', password='testpass123')
		self.client.force_authenticate(user=self.user)

	def test_challenge_response_has_compatibility_fields(self):
		today = timezone.localdate()
		challenge = Challenge.objects.create(
			title='10K Steps Sprint',
			description='Daily step sprint',
			challenge_type='steps',
			target_value=10000,
			target_unit='steps',
			start_date=today,
			end_date=today,
			status='active',
			created_by=self.user,
			is_public=True,
		)
		ChallengeParticipant.objects.create(user=self.user, challenge=challenge, cached_progress=2500)

		response = self.client.get('/api/v1/community/challenges/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		item = response.data[0]
		self.assertEqual(item['name'], '10K Steps Sprint')
		self.assertTrue(item['joined'])
		self.assertIn('progress', item)


class CommunityFeedAndChatTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='feed-user@example.com', password='testpass123')
		self.other = User.objects.create_user(email='other@example.com', password='testpass123')
		self.client.force_authenticate(user=self.user)
		self.group = CommunityGroup.objects.create(
			name='Chat Group',
			created_by=self.user,
			is_public=True,
		)
		GroupMembership.objects.create(user=self.user, group=self.group, role='admin')

	def test_create_like_and_comment_feed_post(self):
		create_resp = self.client.post(
			'/api/v1/community/feed/',
			{'content': 'Morning walk done!'},
			format='json',
		)
		self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
		post_id = create_resp.data['id']

		like_resp = self.client.post(f'/api/v1/community/feed/{post_id}/like/', {}, format='json')
		self.assertEqual(like_resp.status_code, status.HTTP_200_OK)
		self.assertTrue(like_resp.data['liked'])

		comment_resp = self.client.post(
			f'/api/v1/community/feed/{post_id}/comments/',
			{'content': 'Great effort!'},
			format='json',
		)
		self.assertEqual(comment_resp.status_code, status.HTTP_201_CREATED)

		self.assertEqual(CommunityPost.objects.count(), 1)
		self.assertEqual(CommunityPostReaction.objects.filter(post_id=post_id, is_active=True).count(), 1)
		self.assertEqual(CommunityPostComment.objects.filter(post_id=post_id, is_deleted=False).count(), 1)

	def test_group_chat_send_and_list(self):
		send_resp = self.client.post(
			f'/api/v1/community/groups/{self.group.id}/chat/',
			{'content': 'Hello team'},
			format='json',
		)
		self.assertEqual(send_resp.status_code, status.HTTP_201_CREATED)

		list_resp = self.client.get(f'/api/v1/community/groups/{self.group.id}/chat/')
		self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_resp.data), 1)
		self.assertEqual(list_resp.data[0]['content'], 'Hello team')
		self.assertEqual(GroupChatMessage.objects.filter(group=self.group, is_deleted=False).count(), 1)


class CommunityEnhancementTests(APITestCase):
	def setUp(self):
		self.owner = User.objects.create_user(email='owner2@example.com', password='testpass123')
		self.member = User.objects.create_user(email='member2@example.com', password='testpass123')
		self.client.force_authenticate(user=self.owner)
		self.group = CommunityGroup.objects.create(
			name='Enhancement Group',
			created_by=self.owner,
			is_public=True,
		)
		GroupMembership.objects.create(user=self.owner, group=self.group, role='admin')
		GroupMembership.objects.create(user=self.member, group=self.group, role='member')

	def test_milestone_sync_creates_feed_post_and_badge(self):
		today = timezone.localdate()
		DailyStepLog.objects.create(
			user=self.owner,
			date=today,
			manual_steps=6000,
			synced_steps=0,
		)

		response = self.client.post('/api/v1/community/feed/milestones/sync/', {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(response.data['created_count'], 1)
		self.assertTrue(
			CommunityPost.objects.filter(user=self.owner, post_type='milestone').exists()
		)
		self.assertTrue(UserBadge.objects.filter(user=self.owner).exists())

	def test_admin_can_update_group_member_role(self):
		response = self.client.post(
			f'/api/v1/community/groups/{self.group.id}/roles/',
			{'member_id': str(self.member.id), 'role': 'moderator'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		membership = GroupMembership.objects.get(user=self.member, group=self.group)
		self.assertEqual(membership.role, 'moderator')

	def test_chat_mentions_create_notification_and_unread(self):
		response = self.client.post(
			f'/api/v1/community/groups/{self.group.id}/chat/',
			{'content': f'Hello @{self.member.email}'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(
			CommunityNotification.objects.filter(
				user=self.member,
				title='You were mentioned in group chat',
			).exists()
		)

		self.client.force_authenticate(user=self.member)
		unread_resp = self.client.get('/api/v1/community/groups/chat/unread/')
		self.assertEqual(unread_resp.status_code, status.HTTP_200_OK)
		self.assertEqual(len(unread_resp.data), 1)
		self.assertTrue(unread_resp.data[0]['has_unread'])

	def test_mute_all_preference_blocks_new_notifications(self):
		new_user = User.objects.create_user(email='newjoiner@example.com', password='testpass123')
		UserCommunityPreference.objects.create(user=self.owner, mute_all=True)
		self.client.force_authenticate(user=new_user)
		response = self.client.post(
			'/api/v1/community/groups/join/',
			{'group_id': str(self.group.id)},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse(
			CommunityNotification.objects.filter(
				user=self.owner,
				notification_type='group_joined',
			).exists()
		)
