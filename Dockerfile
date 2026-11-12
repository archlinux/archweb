FROM archlinux:latest

RUN pacman -Syu --noconfirm --needed git python uv wget && pacman -Scc --noconfirm

WORKDIR /app

# Keep the virtualenv outside /app so it survives bind-mounting the source
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

# Fetch the style submodule if it was not initialized in the build context
RUN [ -e archlinux_common_style/django ] || \
    (rm -rf archlinux_common_style && \
     git clone --depth 1 https://gitlab.archlinux.org/archlinux/archlinux-common-style.git archlinux_common_style)

RUN cp local_settings.py.example local_settings.py && \
    sed -i 's/^DEBUG = False/DEBUG = True/' local_settings.py

EXPOSE 8000

CMD ["sh", "-c", "uv run ./manage.py migrate && \
    uv run ./manage.py loaddata main/fixtures/*.json devel/fixtures/*.json mirrors/fixtures/*.json releng/fixtures/*.json && \
    uv run ./manage.py runserver 0.0.0.0:8000"]
