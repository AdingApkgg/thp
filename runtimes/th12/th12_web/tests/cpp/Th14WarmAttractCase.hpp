#pragma once

// Test-case initialization only. The original observer clears attract bit40
// once, after copying the first pre-Player snapshot. These convenience flags
// and the ECL-visible flags cell represent that same original bit in C++.
// Ordinary attract mode must retain its normal behavior outside this fixture.
struct Th14WarmAttractCase {
    bool pending=false;
    void arm()noexcept{pending=true;}
    template<class Session> bool after_player_snapshot(Session& session)noexcept{
        if(!pending)return true;
        if(!session.battle)return false;
        session.state.demo=false;
        session.battle->demo=false;
        session.battle->enemy_commands.th14_run_flags&=~0x40u;
        pending=false;
        return true;
    }
};
