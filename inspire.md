Looking at your code, you're currently using Google's Gemini API for image generation with text prompts only. Good news: Yes, Gemini supports multimodal inputs, meaning you can upload an inspiration image to influence the style and colors of generated images.
Current Implementation Analysis
Your code currently:

Uses genai.Client with generate_content()
Passes only text in contents=[prompt]
Uses ImageConfig for aspect ratio and resolution
Has a style_context parameter (but it's just appended to text)

How to Add Inspiration Image Support
Here's how you can modify your code to accept an inspiration image:
pythondef generate_image_bytes(
    self,
    prompt: str,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    style_context: Optional[str] = None,
    inspiration_image: Optional[Path | bytes | Image.Image] = None,  # NEW
) -> bytes:
    """Generate an image from a prompt and return bytes."""
    
    # Build the content list
    content_parts = []
    
    # Add inspiration image first if provided
    if inspiration_image:
        if isinstance(inspiration_image, Path):
            # Load from file
            with open(inspiration_image, 'rb') as f:
                image_bytes = f.read()
            content_parts.append(types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png"  # or detect from file extension
            ))
        elif isinstance(inspiration_image, bytes):
            content_parts.append(types.Part.from_bytes(
                data=inspiration_image,
                mime_type="image/png"
            ))
        elif isinstance(inspiration_image, Image.Image):
            buffer = io.BytesIO()
            inspiration_image.save(buffer, format="PNG")
            content_parts.append(types.Part.from_bytes(
                data=buffer.getvalue(),
                mime_type="image/png"
            ))
    
    # Build the text prompt
    text_prompt = prompt
    if style_context:
        text_prompt = f"{text_prompt}\n\nStyle guide: {style_context}"
    
    # Add instruction for style transfer if image provided
    if inspiration_image:
        text_prompt = f"{text_prompt}\n\nUse the colors, style, and aesthetic of the reference image provided above."
    
    content_parts.append(text_prompt)
    
    logger.debug("Image generation prompt: %s", text_prompt)
    logger.info("Image generation prompt:\n%s", text_prompt)
    sys.stdout.write(f"[Image prompt]\n{text_prompt}\n\n")
    sys.stdout.flush()
    
    model_name = model or self.model
    aspect = aspect_ratio or settings.gemini_image_aspect_ratio
    image_size = resolution or settings.gemini_image_resolution
    
    logger.info(
        "Generating image model=%s aspect=%s size=%s with_reference=%s",
        model_name,
        aspect,
        image_size,
        inspiration_image is not None,
    )
    
    response = self.client.models.generate_content(
        model=model_name,
        contents=content_parts,  # Changed from [prompt] to content_parts
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect,
                image_size=image_size,
            ),
        ),
    )
    
    # Rest of the code remains the same...
Update save_shot_image Method
pythondef save_shot_image(
    self,
    project_dir: Path,
    scene_number: int,
    shot_number: int,
    prompt: str,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    style_context: Optional[str] = None,
    inspiration_image: Optional[Path | bytes | Image.Image] = None,  # NEW
) -> Path:
    """Generate and save a shot image under the project directory."""
    image_bytes = self.generate_image_bytes(
        prompt,
        model=model,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        style_context=style_context,
        inspiration_image=inspiration_image,  # NEW
    )
    # Rest remains the same...
Important Considerations

Model Compatibility: Ensure you're using a Gemini model that supports image generation with multimodal inputs (like gemini-2.0-flash-exp or newer image generation models)
Prompt Engineering: You'll want to be explicit in your text prompt about what you want from the reference image:

"Match the color palette"
"Use the same artistic style"
"Replicate the lighting and atmosphere"


Check Latest Docs: Since Google's Gemini API evolves rapidly, check the latest documentation at https://ai.google.dev/gemini-api/docs/vision for the most current capabilities and best practices
Alternative: Some Gemini models might have specific image editing or style transfer modes - check if there are specialized parameters in ImageConfig for this use case

Would you like me to help you implement this with a specific example or test it with your current setup?