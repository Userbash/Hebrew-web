#!/usr/bin/env bash
set -e

echo "== Fix Codex CLI for Bazzite + Flatpak VS Code =="

# 1. Проверка Node/npm
if ! command -v npm >/dev/null 2>&1; then
  echo "npm не найден. Установи Node.js/npm через toolbox:"
  echo "toolbox create -y"
  echo "toolbox enter"
  echo "sudo dnf install nodejs npm -y"
  exit 1
fi

# 2. Настраиваем npm global в домашнюю папку
mkdir -p "$HOME/.npm-global"
npm config set prefix "$HOME/.npm-global"

# 3. Добавляем PATH
mkdir -p "$HOME/.local/bin"

for shellrc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  touch "$shellrc"
  if ! grep -q '.npm-global/bin' "$shellrc"; then
    echo 'export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"' >> "$shellrc"
  fi
done

export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

# 4. Переустанавливаем Codex CLI
npm uninstall -g @openai/codex >/dev/null 2>&1 || true
npm install -g @openai/codex

# 5. Создаём wrapper
cat > "$HOME/.local/bin/codex" <<EOF
#!/usr/bin/env bash
export PATH="\$HOME/.npm-global/bin:\$HOME/.local/bin:\$PATH"
exec "\$HOME/.npm-global/bin/codex" "\$@"
EOF

chmod +x "$HOME/.local/bin/codex"

# 6. Чиним Flatpak VS Code PATH
if command -v flatpak >/dev/null 2>&1; then
  if flatpak list --app | grep -q "com.visualstudio.code"; then
    flatpak override --user \
      --env=PATH="$HOME/.npm-global/bin:$HOME/.local/bin:/app/bin:/usr/bin:/bin" \
      com.visualstudio.code
    echo "Flatpak override применён для com.visualstudio.code"
  else
    echo "Flatpak VS Code com.visualstudio.code не найден. Пропускаю override."
  fi
fi

echo
echo "Готово."
echo "Закрой VS Code полностью и открой заново."
echo "Потом проверь:"
echo "codex --version"
echo "codex"
