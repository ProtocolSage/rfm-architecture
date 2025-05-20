# Animation System

RFM Architecture includes a powerful animation system for creating dynamic visualizations of the Recursive Fractal Mind. This document describes the animation capabilities and how to configure them.

## Animation Types

The animation system supports several types of animations:

- **Broadcast Animation**: Simulates information broadcast throughout the architecture
- **Particle Flow**: Creates flowing particle effects between components
- **Pulsing Effects**: Pulsing/glowing effects for components
- **Morphing Fractals**: Smoothly transitions between fractal parameters

## Broadcast Animation

Broadcast animation simulates the global workspace theory concept of information broadcasting throughout the cognitive architecture.

### Configuration

```yaml
animation:
  broadcast:
    enabled: true        # Enable broadcast animation
    duration: 400        # Animation duration in milliseconds
    fps: 60              # Frames per second
    pulse_count: 3       # Number of pulses
    easing: "cubic-bezier(0.25, 0.1, 0.25, 1.0)"  # CSS-style easing function
    color: "#00c2c7"     # Pulse color
    glow: true           # Enable glow effect
```

## Animation Timeline

The animation system uses a timeline-based approach for sequencing animations:

```python
from rfm.viz.animation_engine import AnimationTimeline, BroadcastSequence

# Create a timeline
timeline = AnimationTimeline(fps=60, duration=10000)  # 10 seconds

# Add broadcast sequence
timeline.add_sequence(
    BroadcastSequence(
        source="cif",           # Source component
        targets=["perception", "knowledge", "metacognitive"],  # Target components
        start_time=1000,        # Start time in milliseconds
        duration=2000,          # Duration in milliseconds
        color="#00c2c7",        # Pulse color
        pulse_count=3,          # Number of pulses
        easing="ease-out"       # Easing function
    )
)

# Add another sequence
timeline.add_sequence(
    BroadcastSequence(
        source="metacognitive",
        targets=["evolutionary", "simulation"],
        start_time=3500,
        duration=1500,
        color="#f5a742",
        pulse_count=2,
        easing="ease-in-out"
    )
)

# Render the animation
timeline.render(output_path="animation.gif", format="gif")
```

## Particle Flow System

The particle flow system creates dynamic particle animations between components:

```python
from rfm.viz.animation_engine import ParticleFlowSystem

# Create a particle flow system
flow = ParticleFlowSystem(
    source="perception",     # Source component
    target="cif",            # Target component
    particle_count=50,       # Number of particles
    speed=2.0,               # Particle speed
    color="#4287f5",         # Particle color
    size_range=(1, 3),       # Min/max particle size
    trail_length=5,          # Length of particle trail
    jitter=0.2               # Random movement factor
)

# Add to timeline
timeline.add_sequence(flow, start_time=500, duration=3000)
```

## Running Animations

To run an animation, you can use the `animate_rfm.py` script:

```bash
python animate_rfm.py --output animation.gif --format gif --duration 10
```

Or create your own animation script:

```python
from rfm.config.settings import ConfigLoader
from rfm.viz.animation_engine import AnimationTimeline, create_animation

# Load configuration
config = ConfigLoader.from_file("config.yaml")

# Create and run animation
timeline = create_animation(config)
timeline.render("animation.gif", format="gif")
```

## Export Formats

The animation system supports exporting to several formats:

- **GIF**: Animated GIF (universal support, larger file size)
- **MP4**: H.264 video (smaller file size, good quality)
- **WebM**: VP9 video (good for web)
- **HTML**: Interactive HTML animation with JavaScript

Example:

```python
# Export to different formats
timeline.render("animation.gif", format="gif")
timeline.render("animation.mp4", format="mp4", quality=80)
timeline.render("animation.webm", format="webm")
timeline.render("animation.html", format="html")
```

## Animation Parameters

The following parameters can be used to customize animations:

### Global Parameters

- **fps**: Frames per second (higher values = smoother animation, larger file size)
- **duration**: Total animation duration in milliseconds
- **background**: Background color (hex code)
- **loop**: Whether the animation should loop (boolean)

### Broadcast Parameters

- **color**: Color of the broadcast pulse (hex code)
- **pulse_count**: Number of pulses to emit
- **easing**: Easing function for the animation
- **glow**: Whether to add a glow effect
- **glow_color**: Color of the glow effect
- **glow_radius**: Radius of the glow effect

### Particle Flow Parameters

- **particle_count**: Number of particles
- **speed**: Particle speed
- **color**: Particle color
- **size_range**: Range of particle sizes (min, max)
- **trail_length**: Length of particle trail
- **jitter**: Random movement factor