def build_creative_brief(platform, profile, mood, ml_pred, audio_feat, lyrics):
    return {
        "platform": platform,
        "mood": mood,
        "audio_features": audio_feat,
        "ml_predictions": ml_pred,
        "lyrics": lyrics,
        "platform_profile": profile
    }
