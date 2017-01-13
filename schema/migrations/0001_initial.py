# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Post'
        db.create_table('murmur_posts', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'], null=True)),
            ('subject', self.gf('django.db.models.fields.TextField')()),
            ('msg_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=120)),
            ('post', self.gf('django.db.models.fields.TextField')()),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Thread'])),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')(related_name='replies', null=True, to=orm['schema.Post'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('forwarding_list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.ForwardingList'], null=True)),
            ('poster_email', self.gf('django.db.models.fields.EmailField')(max_length=255, null=True)),
        ))
        db.send_create_signal(u'schema', ['Post'])

        # Adding model 'Thread'
        db.create_table('murmur_threads', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.TextField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
        ))
        db.send_create_signal(u'schema', ['Thread'])

        # Adding model 'TagThread'
        db.create_table(u'schema_tagthread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Thread'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Tag'])),
        ))
        db.send_create_signal(u'schema', ['TagThread'])

        # Adding unique constraint on 'TagThread', fields ['thread', 'tag']
        db.create_unique(u'schema_tagthread', ['thread_id', 'tag_id'])

        # Adding model 'Tag'
        db.create_table(u'schema_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'schema', ['Tag'])

        # Adding unique constraint on 'Tag', fields ['name', 'group']
        db.create_unique(u'schema_tag', ['name', 'group_id'])

        # Adding model 'FollowTag'
        db.create_table(u'schema_followtag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Tag'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['FollowTag'])

        # Adding unique constraint on 'FollowTag', fields ['user', 'tag']
        db.create_unique(u'schema_followtag', ['user_id', 'tag_id'])

        # Adding model 'MuteTag'
        db.create_table(u'schema_mutetag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Tag'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['MuteTag'])

        # Adding unique constraint on 'MuteTag', fields ['user', 'tag']
        db.create_unique(u'schema_mutetag', ['user_id', 'tag_id'])

        # Adding model 'MemberGroup'
        db.create_table('murmur_membergroups', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('admin', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('moderator', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('no_emails', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('always_follow_thread', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('upvote_emails', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'schema', ['MemberGroup'])

        # Adding unique constraint on 'MemberGroup', fields ['member', 'group']
        db.create_unique('murmur_membergroups', ['member_id', 'group_id'])

        # Adding model 'ForwardingList'
        db.create_table(u'schema_forwardinglist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=255)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Group'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('can_post', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_receive', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'schema', ['ForwardingList'])

        # Adding model 'Group'
        db.create_table('murmur_groups', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('allow_attachments', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['Group'])

        # Adding model 'UserProfile'
        db.create_table(u'schema_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=255)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_admin', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['UserProfile'])

        # Adding model 'Following'
        db.create_table('murmur_following', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Thread'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['Following'])

        # Adding model 'Mute'
        db.create_table('murmur_mute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Thread'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['Mute'])

        # Adding model 'Upvote'
        db.create_table('murmur_likes', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.Post'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.UserProfile'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'schema', ['Upvote'])


    def backwards(self, orm):
        # Removing unique constraint on 'MemberGroup', fields ['member', 'group']
        db.delete_unique('murmur_membergroups', ['member_id', 'group_id'])

        # Removing unique constraint on 'MuteTag', fields ['user', 'tag']
        db.delete_unique(u'schema_mutetag', ['user_id', 'tag_id'])

        # Removing unique constraint on 'FollowTag', fields ['user', 'tag']
        db.delete_unique(u'schema_followtag', ['user_id', 'tag_id'])

        # Removing unique constraint on 'Tag', fields ['name', 'group']
        db.delete_unique(u'schema_tag', ['name', 'group_id'])

        # Removing unique constraint on 'TagThread', fields ['thread', 'tag']
        db.delete_unique(u'schema_tagthread', ['thread_id', 'tag_id'])

        # Deleting model 'Post'
        db.delete_table('murmur_posts')

        # Deleting model 'Thread'
        db.delete_table('murmur_threads')

        # Deleting model 'TagThread'
        db.delete_table(u'schema_tagthread')

        # Deleting model 'Tag'
        db.delete_table(u'schema_tag')

        # Deleting model 'FollowTag'
        db.delete_table(u'schema_followtag')

        # Deleting model 'MuteTag'
        db.delete_table(u'schema_mutetag')

        # Deleting model 'MemberGroup'
        db.delete_table('murmur_membergroups')

        # Deleting model 'ForwardingList'
        db.delete_table(u'schema_forwardinglist')

        # Deleting model 'Group'
        db.delete_table('murmur_groups')

        # Deleting model 'UserProfile'
        db.delete_table(u'schema_userprofile')

        # Deleting model 'Following'
        db.delete_table('murmur_following')

        # Deleting model 'Mute'
        db.delete_table('murmur_mute')

        # Deleting model 'Upvote'
        db.delete_table('murmur_likes')


    models = {
        u'schema.following': {
            'Meta': {'object_name': 'Following', 'db_table': "'murmur_following'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Thread']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']"})
        },
        u'schema.followtag': {
            'Meta': {'unique_together': "(('user', 'tag'),)", 'object_name': 'FollowTag'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Tag']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']"})
        },
        u'schema.forwardinglist': {
            'Meta': {'object_name': 'ForwardingList'},
            'can_post': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_receive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'schema.group': {
            'Meta': {'object_name': 'Group', 'db_table': "'murmur_groups'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'allow_attachments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'schema.membergroup': {
            'Meta': {'unique_together': "(('member', 'group'),)", 'object_name': 'MemberGroup', 'db_table': "'murmur_membergroups'"},
            'admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'always_follow_thread': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']"}),
            'moderator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'no_emails': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'upvote_emails': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'schema.mute': {
            'Meta': {'object_name': 'Mute', 'db_table': "'murmur_mute'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Thread']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']"})
        },
        u'schema.mutetag': {
            'Meta': {'unique_together': "(('user', 'tag'),)", 'object_name': 'MuteTag'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Tag']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']"})
        },
        u'schema.post': {
            'Meta': {'ordering': "['timestamp']", 'object_name': 'Post', 'db_table': "'murmur_posts'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']", 'null': 'True'}),
            'forwarding_list': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.ForwardingList']", 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msg_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '120'}),
            'post': ('django.db.models.fields.TextField', [], {}),
            'poster_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'null': 'True'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'replies'", 'null': 'True', 'to': u"orm['schema.Post']"}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Thread']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'schema.tag': {
            'Meta': {'unique_together': "(('name', 'group'),)", 'object_name': 'Tag'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'schema.tagthread': {
            'Meta': {'unique_together': "(('thread', 'tag'),)", 'object_name': 'TagThread'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Tag']"}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Thread']"})
        },
        u'schema.thread': {
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'Thread', 'db_table': "'murmur_threads'"},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'schema.upvote': {
            'Meta': {'object_name': 'Upvote', 'db_table': "'murmur_likes'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.Post']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schema.UserProfile']"})
        },
        u'schema.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['schema']