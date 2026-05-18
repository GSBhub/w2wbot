from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from datetime import datetime, timedelta
import discord
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import w2wbot


@pytest.fixture(autouse=True)
def reset_bot_globals():
    orig_session_start = w2wbot.session_start
    orig_last_posted = w2wbot.last_posted_message_time
    orig_team = w2wbot.team_name
    orig_location = w2wbot.location
    w2wbot.session_start = datetime.now()
    w2wbot.last_posted_message_time = None
    w2wbot.team_name = "My Team"
    w2wbot.location = 123
    yield
    w2wbot.session_start = orig_session_start
    w2wbot.last_posted_message_time = orig_last_posted
    w2wbot.team_name = orig_team
    w2wbot.location = orig_location


# Helper: turn a plain list into an async iterable for mocking channel.history()
async def async_messages(messages):
    for msg in messages:
        yield msg


class TestShouldPost:
    def test_posts_when_never_posted(self):
        assert w2wbot.should_post(None) is True

    def test_skip_first_week_suppresses_post(self):
        assert w2wbot.should_post(datetime.now()) is False

    def test_posts_after_7_days(self):
        assert w2wbot.should_post(datetime.now() - timedelta(days=7)) is True

    def test_no_post_within_7_days(self):
        assert w2wbot.should_post(datetime.now() - timedelta(days=6)) is False

    def test_posts_at_exactly_7_days(self):
        assert w2wbot.should_post(datetime.now() - timedelta(days=7, seconds=1)) is True


class TestNextGameMessage:
    def test_home_team(self):
        mock_game = ["Mon 03/15 10:00 AM", "Field 1", "My Team", "Opponent", ""]
        with patch("w2wbot.getNextGame", return_value=mock_game):
            msg = w2wbot.next_game_message("My Team", 123)
        assert "My Team" in msg
        assert "Opponent" in msg
        assert "home team" in msg

    def test_away_team(self):
        mock_game = ["Mon 03/15 10:00 AM", "Field 1", "Opponent", "My Team", ""]
        with patch("w2wbot.getNextGame", return_value=mock_game):
            msg = w2wbot.next_game_message("My Team", 123)
        assert "away team" in msg

    def test_no_game_returns_empty_string(self):
        with patch("w2wbot.getNextGame", return_value=None):
            msg = w2wbot.next_game_message("My Team", 123)
        assert msg == ""

    def test_force_message_when_no_game(self):
        with patch("w2wbot.getNextGame", return_value=None):
            msg = w2wbot.next_game_message("My Team", 123, force_message=True)
        assert msg != ""

    def test_includes_field(self):
        mock_game = ["Mon 03/15 10:00 AM", "Field 5", "My Team", "Opponent", ""]
        with patch("w2wbot.getNextGame", return_value=mock_game):
            msg = w2wbot.next_game_message("My Team", 123)
        assert "Field 5" in msg


class TestPrevGameMessage:
    def test_home_team_with_score(self):
        mock_game = ["Mon 03/08 10:00 AM", "Field 1", "My Team", "Opponent", "3-1"]
        with patch("w2wbot.getPreviousGame", return_value=mock_game):
            msg = w2wbot.prev_game_message("My Team", 123)
        assert "My Team" in msg
        assert "3-1" in msg
        assert "home team" in msg

    def test_away_team(self):
        mock_game = ["Mon 03/08 10:00 AM", "Field 1", "Opponent", "My Team", "2-2"]
        with patch("w2wbot.getPreviousGame", return_value=mock_game):
            msg = w2wbot.prev_game_message("My Team", 123)
        assert "away team" in msg

    def test_no_game_returns_empty_string(self):
        with patch("w2wbot.getPreviousGame", return_value=None):
            msg = w2wbot.prev_game_message("My Team", 123)
        assert msg == ""

    def test_force_message_when_no_game(self):
        with patch("w2wbot.getPreviousGame", return_value=None):
            msg = w2wbot.prev_game_message("My Team", 123, force_message=True)
        assert msg != ""

    def test_includes_score(self):
        mock_game = ["Mon 03/08 10:00 AM", "Field 1", "My Team", "Opponent", "5-0"]
        with patch("w2wbot.getPreviousGame", return_value=mock_game):
            msg = w2wbot.prev_game_message("My Team", 123)
        assert "5-0" in msg


class TestBuildScheduleMessage:
    MOCK_SCHEDULE = [
        ["Mon 03/15 10:00 AM", "Field 1", "My Team", "Opponent A", ""],
        ["Mon 03/22 10:00 AM", "Field 2", "Opponent B", "My Team", ""],
    ]

    def test_returns_embed_when_schedule_exists(self):
        with patch("w2wbot.getSchedule", return_value=iter(self.MOCK_SCHEDULE)):
            msg, _ = w2wbot.build_schedule_message("My Team", 123)
        assert msg is not None

    def test_returns_none_for_empty_schedule(self):
        with patch("w2wbot.getSchedule", return_value=iter([])):
            msg, _ = w2wbot.build_schedule_message("My Team", 123)
        assert msg is None

    def test_new_session_when_start_date_changes(self):
        w2wbot.session_start = datetime(2025, 1, 1)
        with patch("w2wbot.getSchedule", return_value=iter(self.MOCK_SCHEDULE)):
            _, new_session = w2wbot.build_schedule_message("My Team", 123)
        assert new_session is True

    def test_no_new_session_same_start_date(self):
        w2wbot.session_start = datetime(datetime.now().year, 3, 15)
        with patch("w2wbot.getSchedule", return_value=iter(self.MOCK_SCHEDULE)):
            _, new_session = w2wbot.build_schedule_message("My Team", 123)
        assert new_session is False

    def test_embed_title_contains_team_name(self):
        with patch("w2wbot.getSchedule", return_value=iter(self.MOCK_SCHEDULE)):
            msg, _ = w2wbot.build_schedule_message("My Team", 123)
        assert "MY TEAM" in msg.title


class TestGetLastScheduleMessage:
    async def test_returns_none_for_empty_history(self):
        mock_channel = MagicMock()
        mock_channel.history.return_value = async_messages([])
        result = await w2wbot.get_last_schedule_message(mock_channel)
        assert result is None

    async def test_finds_schedule_embed_message(self):
        bot_user = MagicMock()
        embed = MagicMock()
        embed.title = "MY TEAM's Schedule"
        sched_msg = MagicMock(author=bot_user, embeds=[embed])

        mock_channel = MagicMock()
        mock_channel.history.return_value = async_messages([sched_msg])

        with patch.object(type(w2wbot.client), "user",
                          new_callable=PropertyMock, return_value=bot_user):
            result = await w2wbot.get_last_schedule_message(mock_channel)
        assert result is sched_msg

    async def test_skips_plain_text_bot_messages(self):
        bot_user = MagicMock()
        plain_msg = MagicMock(author=bot_user, embeds=[])

        mock_channel = MagicMock()
        mock_channel.history.return_value = async_messages([plain_msg])

        with patch.object(type(w2wbot.client), "user",
                          new_callable=PropertyMock, return_value=bot_user):
            result = await w2wbot.get_last_schedule_message(mock_channel)
        assert result is None

    async def test_skips_bot_messages_with_non_schedule_embeds(self):
        bot_user = MagicMock()
        embed = MagicMock()
        embed.title = "Something Else"
        other_msg = MagicMock(author=bot_user, embeds=[embed])

        mock_channel = MagicMock()
        mock_channel.history.return_value = async_messages([other_msg])

        with patch.object(type(w2wbot.client), "user",
                          new_callable=PropertyMock, return_value=bot_user):
            result = await w2wbot.get_last_schedule_message(mock_channel)
        assert result is None

    async def test_skips_schedule_embeds_from_other_users(self):
        bot_user = MagicMock()
        other_user = MagicMock()
        embed = MagicMock()
        embed.title = "MY TEAM's Schedule"
        foreign_msg = MagicMock(author=other_user, embeds=[embed])

        mock_channel = MagicMock()
        mock_channel.history.return_value = async_messages([foreign_msg])

        with patch.object(type(w2wbot.client), "user",
                          new_callable=PropertyMock, return_value=bot_user):
            result = await w2wbot.get_last_schedule_message(mock_channel)
        assert result is None

    async def test_returns_first_match_in_history(self):
        bot_user = MagicMock()
        embed1 = MagicMock()
        embed1.title = "MY TEAM's Schedule"
        embed2 = MagicMock()
        embed2.title = "MY TEAM's Schedule"
        newer_msg = MagicMock(author=bot_user, embeds=[embed1])
        older_msg = MagicMock(author=bot_user, embeds=[embed2])

        mock_channel = MagicMock()
        # history returns newest first
        mock_channel.history.return_value = async_messages([newer_msg, older_msg])

        with patch.object(type(w2wbot.client), "user",
                          new_callable=PropertyMock, return_value=bot_user):
            result = await w2wbot.get_last_schedule_message(mock_channel)
        assert result is newer_msg


class TestSlashCommandHandlers:
    """Test slash command handler logic via mocked discord.Interaction objects."""

    def _mock_interaction(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        return interaction

    async def test_next_command_sends_next_game(self):
        interaction = self._mock_interaction()
        mock_game = ["Mon 03/15 10:00 AM", "Field 1", "My Team", "Opponent", ""]
        with patch("w2wbot.getNextGame", return_value=mock_game):
            await w2wbot.next_command.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        msg = interaction.response.send_message.call_args.args[0]
        assert "My Team" in msg and "Opponent" in msg

    async def test_next_command_force_message_when_no_game(self):
        interaction = self._mock_interaction()
        with patch("w2wbot.getNextGame", return_value=None):
            await w2wbot.next_command.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        msg = interaction.response.send_message.call_args.args[0]
        assert msg != ""

    async def test_last_command_sends_previous_game(self):
        interaction = self._mock_interaction()
        mock_game = ["Mon 03/08 10:00 AM", "Field 1", "My Team", "Opponent", "3-1"]
        with patch("w2wbot.getPreviousGame", return_value=mock_game):
            await w2wbot.last_command.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        msg = interaction.response.send_message.call_args.args[0]
        assert "3-1" in msg

    async def test_last_command_force_message_when_no_game(self):
        interaction = self._mock_interaction()
        with patch("w2wbot.getPreviousGame", return_value=None):
            await w2wbot.last_command.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        msg = interaction.response.send_message.call_args.args[0]
        assert msg != ""

    async def test_schedule_command_sends_embed(self):
        interaction = self._mock_interaction()
        mock_schedule = [["Mon 03/15 10:00 AM", "Field 1", "My Team", "Opponent", ""]]
        with patch("w2wbot.getSchedule", return_value=iter(mock_schedule)):
            await w2wbot.schedule_command.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        assert "embed" in interaction.response.send_message.call_args.kwargs

    async def test_schedule_command_embed_has_team_title(self):
        interaction = self._mock_interaction()
        mock_schedule = [["Mon 03/15 10:00 AM", "Field 1", "My Team", "Opponent", ""]]
        with patch("w2wbot.getSchedule", return_value=iter(mock_schedule)):
            await w2wbot.schedule_command.callback(interaction)
        embed = interaction.response.send_message.call_args.kwargs["embed"]
        assert "MY TEAM" in embed.title


class TestSlashCommandRegistration:
    def test_last_command_registered(self):
        names = [cmd.name for cmd in w2wbot.tree.get_commands()]
        assert "last" in names

    def test_next_command_registered(self):
        names = [cmd.name for cmd in w2wbot.tree.get_commands()]
        assert "next" in names

    def test_schedule_command_registered(self):
        names = [cmd.name for cmd in w2wbot.tree.get_commands()]
        assert "schedule" in names

    def test_all_three_commands_present(self):
        names = [cmd.name for cmd in w2wbot.tree.get_commands()]
        assert len([n for n in names if n in ("last", "next", "schedule")]) == 3
