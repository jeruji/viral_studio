from audio_remix.remix_engine import RemixPlan

def preset_jedag_jedug(src_bpm: float, drum_loop: str | None):
    return RemixPlan(
        target_bpm=min(160.0, src_bpm * 1.10),
        bass_boost_db=6.5,
        presence_boost_db=2.0,
        limiter_ceiling=0.98,
        drum_loop_path=drum_loop,
        drum_mix_db=-9.0,
    )

def preset_tiktok_house(src_bpm: float, drum_loop: str | None):
    return RemixPlan(
        target_bpm=128.0,
        bass_boost_db=5.0,
        presence_boost_db=2.5,
        limiter_ceiling=0.97,
        drum_loop_path=drum_loop,
        drum_mix_db=-10.0,
    )

def preset_mellow_rainy():
    return RemixPlan(
        target_bpm=None,
        bass_boost_db=2.0,
        presence_boost_db=0.8,
        limiter_ceiling=0.95,
        drum_loop_path=None,
    )

def preset_cinematic_epic():
    return RemixPlan(
        target_bpm=None,
        bass_boost_db=4.0,
        presence_boost_db=1.2,
        limiter_ceiling=0.96,
        drum_loop_path=None,
    )

def preset_lofi_chill():
    return RemixPlan(
        target_bpm=None,
        bass_boost_db=1.5,
        presence_boost_db=0.6,
        limiter_ceiling=0.93,
        drum_loop_path=None,
    )
