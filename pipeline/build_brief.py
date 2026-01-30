def build_creative_brief(platform, profile, mood, ml_pred, audio_feat, lyrics, description, content_type):
    return {
        "platform": platform,
        "mood": mood,
        "audio_features": audio_feat,
        "ml_predictions": ml_pred,
        "content_type": content_type,
        "lyrics": lyrics,
        "description": description,
        "platform_profile": profile
    }
