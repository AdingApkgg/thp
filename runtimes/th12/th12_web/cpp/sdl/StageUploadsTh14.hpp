#pragma once
#include "../game/GameSessionResources.hpp"
#include <array>
#include <utility>

#if PORT_TITLE == 14
namespace th11::sdl {

// Owns only upload work references. The host owns textures and releases them
// after cancel() has removed these references; ANM template preparation stays
// at the core's successful phase-completion boundary.
class StageUploadsTh14 {
public:
    using Phase = StageResourceEffects::Phase;
    struct Job { AnmResource* resource=nullptr; u16 file=0; u32 chunk=0; };

    bool begin(StageResources& stage,Phase phase) {
        if(owner_) {
            if(owner_!=&stage||failed_)return false;
            if(phase_==phase)return true;
            if(pending())return false;
        }
        std::array<Job,5> next{};
        u32 count=0;
        switch(phase) {
        case Phase::Hud:next[count++]={&stage.logo,6};break;
        case Phase::Scene:next[count++]={&stage.background,u16((stage.stage_number&1)+3)};break;
        case Phase::Timeline:
            // 42256a loads exactly the ECL ANIM list at file 10+i.
            // stage.enemies is a legacy duplicate, not another native upload.
            for(u32 i=0;i<stage.ecl_animations.size();++i)
                if(!stage.ecl_animation_names[i].empty())next[count++]={&stage.ecl_animations[i],u16(10+i)};
            break;
        default:return false;
        }
        jobs_=next;owner_=&stage;phase_=phase;queued_=count;cursor_=0;failed_=false;
        return true;
    }

    bool pending()const noexcept {return owner_&&cursor_<queued_;}
    u32 pending_count()const noexcept {return owner_?queued_-cursor_:0;}
    const StageResources* owner()const noexcept {return owner_;}
    bool failed()const noexcept {return failed_;}

    template<class Prepare> bool advance(Prepare&& prepare) {
        if(failed_)return false;
        if(!pending())return true;
        // A failure can follow partial texture preparation. Keep this job and
        // every subsequent resource reference until the host cancels owner_.
        if(!std::forward<Prepare>(prepare)(jobs_[cursor_])) {failed_=true;return false;}
        // Original 47d720 calls 47d230 once: one ANM chunk per pump.
        // The last chunk also initializes templates and clears the file wait.
        auto& job=jobs_[cursor_];
        if(++job.chunk<job.resource->textures.size())return true;
        job={};++cursor_;
        return true;
    }

    bool ready(Phase phase)const noexcept {return owner_&&phase_==phase&&!failed_&&!pending();}
    void finish(StageResources& stage)noexcept {
        if(owner_==&stage&&!failed_&&!pending())clear();
    }
    void cancel(StageResources& stage)noexcept {if(owner_==&stage)clear();}
    void cancel_all()noexcept {clear();}

private:
    void clear()noexcept {jobs_={};owner_=nullptr;queued_=cursor_=0;phase_=Phase::Hud;failed_=false;}
    std::array<Job,5> jobs_{};
    StageResources* owner_=nullptr;
    Phase phase_=Phase::Hud;
    u32 queued_=0,cursor_=0;
    bool failed_=false;
};
}
#endif
