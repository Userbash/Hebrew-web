#!/bin/bash

################################################################################
#                                                                              #
#  УНИВЕРСАЛЬНЫЙ СКРИПТ ПОЛНОЙ АВТОМАТИЗАЦИИ DNS + SSL СЕРТИФИКАТА         #
#  Функции:                                                                   #
#  • Регистрация домена на DuckDNS (автоматическая через API)               #
#  • Получение публичного IP адреса                                          #
#  • Обновление IP на DuckDNS                                                #
#  • Установка acme.sh                                                       #
#  • Получение SSL сертификата (Let's Encrypt)                              #
#  • Автоматическое обновление IP через cron                                #
#  • Автоматическое обновление сертификата через cron                       #
#  • Валидация и проверки на каждом этапе                                   #
#                                                                              #
#  Использование:                                                             #
#  chmod +x auto-setup.sh                                                     #
#  sudo ./auto-setup.sh                                                       #
#                                                                              #
################################################################################

set -e

# ============================================================================ 
#                           КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ
# ============================================================================ 

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Пути и логирование
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/auto-setup"
MAIN_LOG="$LOG_DIR/setup.log"
IP_LOG="$LOG_DIR/ip-updates.log"
SSL_LOG="$LOG_DIR/ssl-updates.log"
CONFIG_DIR="$HOME/.auto-setup-config"
CONFIG_FILE="$CONFIG_DIR/config.env"
LAST_KNOWN_IP_FILE="$CONFIG_DIR/last_known_ip.txt"

# Параметры повторных попыток
RETRIES="${RETRIES:-5}"
RETRY_DELAY="${RETRY_DELAY:-10}" # Задержка в секундах

# Параметры обновления сертификатов
DAYS_TO_RENEWAL="${DAYS_TO_RENEWAL:-30}" # Дней до истечения, когда начинать обновление

# Создание директорий
mkdir -p "$LOG_DIR" "$CONFIG_DIR"

# ============================================================================ 
#                              ФУНКЦИИ ЛОГИРОВАНИЯ
# ============================================================================ 

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$MAIN_LOG"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$MAIN_LOG"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$MAIN_LOG"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$MAIN_LOG"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}" | tee -a "$MAIN_LOG"
}

separator() {
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}" | tee -a "$MAIN_LOG"
}

# ============================================================================ 
#                         ФУНКЦИИ УТИЛИТЫ
# ============================================================================ 

# Функция повторных попыток
retry_cmd() {
    local -r cmd="$@"
    local count=0
    
    until "$cmd"; do
        exit_code=$?
        count=$((count + 1))
        if [ $count -lt "$RETRIES" ]; then
            warning "Команда \"$cmd\" завершилась с ошибкой $exit_code. Повторная попытка через $RETRY_DELAY секунд... (Попытка $count/$RETRIES)"
            sleep "$RETRY_DELAY"
        else
            error "Команда \"$cmd\" завершилась с ошибкой $exit_code после $RETRIES попыток."
            return 1
        fi
    done
    return 0
}

# ============================================================================ 
#                         ФУНКЦИИ ПРОВЕРКИ ЗАВИСИМОСТЕЙ
# ============================================================================ 

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен быть запущен от пользователя root или через sudo"
        exit 1
    fi
    success "Запуск от root"
}

check_dependencies() {
    separator
    log "Проверка зависимостей..."
    
    local missing_deps=()
    
    # Проверить необходимые команды
    for cmd in curl dig git openssl sed awk cron; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
            warning "$cmd не найден"
        else
            success "$cmd установлен"
        fi
    done
    
    # Установка недостающих зависимостей
    if [ ${#missing_deps[@]} -gt 0 ]; then
        warning "Устанавливаю недостающие зависимости: ${missing_deps[*]}"
        
        # Определить систему
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y dnsutils curl git openssl cron
        elif command -v yum &> /dev/null; then
            yum install -y bind-utils curl git openssl cronie
        elif command -v brew &> /dev/null; then
            brew install curl git
        fi
        
        success "Зависимости установлены"
    fi
}

# ============================================================================ 
#                      ФУНКЦИИ РАБОТЫ С КОНФИГУРАЦИЕЙ
# ============================================================================ 

create_config() {
    separator
    log "Создание конфигурационного файла..."
    
    if [ -f "$CONFIG_FILE" ]; then
        warning "Конфигурационный файл уже существует: $CONFIG_FILE"
        read -p "Хотите перезаписать? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Использование существующей конфигурации"
            return 0
        fi
    fi
    
    echo
    echo -e "${CYAN}=== НАЧАЛЬНАЯ НАСТРОЙКА ===${NC}"
    echo
    
    # Запрос email
    read -p "Введите ваш Email (для Let's Encrypt): " EMAIL
    if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        error "Некорректный формат email"
        exit 1
    fi
    success "Email: $EMAIL"
    
    # Запрос имени домена
    echo
    read -p "Введите желаемое имя домена (например: myserver, без .duckdns.org): " DOMAIN_NAME
    DOMAIN_NAME=$(echo "$DOMAIN_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
    
    if [ -z "$DOMAIN_NAME" ]; then
        error "Имя домена не может быть пустым"
        exit 1
    fi
    
    if [ ${#DOMAIN_NAME} -lt 3 ]; then
        error "Имя домена должно быть не менее 3 символов"
        exit 1
    fi
    
    FULL_DOMAIN="$DOMAIN_NAME.duckdns.org"
    success "Полный домен: $FULL_DOMAIN"
    
    # Запрос токена DuckDNS (если есть)
    echo
    echo "У вас есть TOKEN от DuckDNS? Получить его можно на https://www.duckdns.org/"
    read -p "Введите DuckDNS TOKEN (или оставьте пустым для новой регистрации): " DUCKDNS_TOKEN
    
    if [ -z "$DUCKDNS_TOKEN" ]; then
        warning "TOKEN не предоставлен - он будет получен автоматически"
        DUCKDNS_TOKEN="AUTO_GENERATE"
    fi
    
    # Запрос порта (для Nginx/Apache проксирования)
    echo
    read -p "Введите порт приложения для проксирования (или оставьте пустым - 8080): " APP_PORT
    APP_PORT="${APP_PORT:-8080}"
    success "Порт приложения: $APP_PORT"
    
    # Выбор веб-сервера
    echo
    echo "Выберите веб-сервер для HTTPS проксирования:"
    echo "1) Nginx (рекомендуется)"
    echo "2) Apache"
    echo "3) Пока не устанавливать"
    read -p "Выбор (1-3): " WEB_SERVER_CHOICE
    
    case $WEB_SERVER_CHOICE in
        1) WEB_SERVER="nginx" ;;
        2) WEB_SERVER="apache" ;;
        *) WEB_SERVER="none" ;;
    esac
    success "Выбранный веб-сервер: $WEB_SERVER"
    
    # Сохранение конфигурации
    cat > "$CONFIG_FILE" << EOFCONFIG
# Автоматически сгенерирована $(date)
export EMAIL="$EMAIL"
export DOMAIN_NAME="$DOMAIN_NAME"
export FULL_DOMAIN="$FULL_DOMAIN"
export DUCKDNS_TOKEN="$DUCKDNS_TOKEN"
export APP_PORT="$APP_PORT"
export WEB_SERVER="$WEB_SERVER"
export SCRIPT_DIR="$SCRIPT_DIR"
export LOG_DIR="$LOG_DIR"
export MAIN_LOG="$MAIN_LOG"
export IP_LOG="$IP_LOG"
export SSL_LOG="$SSL_LOG"
export CONFIG_DIR="$CONFIG_DIR"
export ACME_HOME="$HOME/.acme.sh"
export RETRIES="$RETRIES"
export RETRY_DELAY="$RETRY_DELAY"
export DAYS_TO_RENEWAL="${DAYS_TO_RENEWAL}"
export LAST_KNOWN_IP_FILE="$LAST_KNOWN_IP_FILE"
EOFCONFIG
    
    chmod 600 "$CONFIG_FILE"
    success "Конфигурация сохранена: $CONFIG_FILE"
    
    # Информативный вывод
    echo
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    cat "$CONFIG_FILE" | grep export | sed 's/export /  • /'
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
}

load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        error "Конфигурационный файл не найден: $CONFIG_FILE"
        error "Сначала запустите конфигурацию"
        exit 1
    fi
    
    source "$CONFIG_FILE"
    success "Конфигурация загружена"
}

# ============================================================================ 
#                      ФУНКЦИИ РАБОТЫ С DuckDNS
# ============================================================================ 

get_public_ip() {
    local ip=""
    
    # Попытка 1: OpenDNS (самый быстрый и надежный)
    if [ -z "$ip" ]; then # No need for retry_cmd here, dig has built-in retry
        ip=$(dig +short myip.opendns.com @resolver1.opendns.com 2>/dev/null)
    fi
    
    if [ -z "$ip" ]; then
        # Попытка 2: Google DNS
        ip=$(dig TXT +short o-o.myaddr.l.google.com @ns1.google.com 2>/dev/null | awk -F'"' '{ print $2}')
    fi
    
    if [ -z "$ip" ]; then
        # Попытка 3: Cloudflare
        ip=$(dig +short txt ch whoami.cloudflare @1.0.0.1 2>/dev/null | tr -d '"')
    fi
    
    if [ -z "$ip" ]; then
        # Попытка 4: ipinfo.io
        ip=$(curl -s ipinfo.io/ip 2>/dev/null)
    fi
    
    if [ -z "$ip" ] || [ "$ip" = "ERROR" ]; then
        error "Не удалось получить публичный IP адрес"
        return 1
    fi
    
    echo "$ip"
}

verify_ip() {
    local ip=$1
    # Проверка валидности IPv4
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        return 0
    else
        return 1
    fi
}

update_duckdns() {
    local token=$1
    local domain=$2
    local ip=$3
    
    log "Отправка запроса на обновление DNS..."
    log "  Domain: $domain"
    log "  IP: $ip"

    local last_known_ip=""
    if [ -f "$LAST_KNOWN_IP_FILE" ]; then
        last_known_ip=$(cat "$LAST_KNOWN_IP_FILE")
    fi

    if [ "$ip" = "$last_known_ip" ]; then
        info "IP адрес не изменился ($ip). Обновление DuckDNS не требуется."
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️ IP не изменился: $domain -> $ip" >> "$IP_LOG"
        return 0
    fi
    
    local response
    if response=$(retry_cmd curl -s "https://www.duckdns.org/update?domains=$domain&token=$token&ip=$ip&verbose=true"); then
        if [[ "$response" == *"OK"* ]]; then
            success "DuckDNS обновлен: $domain -> $ip"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $domain -> $ip" >> "$IP_LOG"
            echo "$ip" > "$LAST_KNOWN_IP_FILE" # Save last known IP
            return 0
        else
            error "Ошибка обновления DuckDNS: $response"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Ошибка: $response" >> "$IP_LOG"
            return 1
        fi
    else
        error "Не удалось обновить DuckDNS после нескольких попыток. Проверьте логи для подробностей."
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Ошибка: Не удалось обновить DuckDNS после нескольких попыток." >> "$IP_LOG"
        return 1
    fi
}

verify_dns() {
    local domain=$1
    
    log "Проверка DNS записи: $domain"
    
    # Попытка получить IP через nslookup
    local dns_ip
    # dig has built-in retry/timeout, no need to wrap in retry_cmd
    dns_ip=$(dig +short "$domain" @8.8.8.8)
    
    if [ -z "$dns_ip" ]; then
        warning "DNS еще не распространился (это нормально, нужно подождать 30-60 секунд)"
        return 1
    fi
    
    success "DNS запись обнаружена: $domain -> $dns_ip"
    return 0
}

test_duckdns_token() {
    local token=$1
    local test_domain="test-$(date +%s)"
    
    log "Проверка валидности DuckDNS TOKEN..."
    
    local response
    if response=$(retry_cmd curl -s "https://www.duckdns.org/update?domains=$test_domain&token=$token&ip=1.1.1.1&verbose=true"); then
        if [[ "$response" == *"OK"* ]] || [[ "$response" == *"NOCHANGE"* ]]; then
            success "DuckDNS TOKEN валиден"
            return 0
        elif [[ "$response" == *"KO"* ]]; then
            error "DuckDNS TOKEN некорректен или невалиден"
            return 1
        else
            error "Неожиданный ответ от DuckDNS: $response"
            return 1
        fi
    else
        error "Не удалось проверить DuckDNS TOKEN после нескольких попыток."
        return 1
    fi
}

# ============================================================================ 
#                      ФУНКЦИИ РАБОТЫ С ACME.SH
# ============================================================================ 

install_acme() {
    separator
    log "Установка acme.sh..."
    
    # Проверить, установлен ли уже
    if command -v acme.sh &> /dev/null; then
        success "acme.sh уже установлен"
        return 0
    fi
    
    # Клонировать репозиторий
    log "Клонирование репозитория acme.sh..."
    cd /tmp
    
    if [ -d "acme.sh" ]; then
        rm -rf acme.sh
    fi
    
    if ! retry_cmd git clone https://github.com/acmesh-official/acme.sh.git; then
        error "Не удалось клонировать репозиторий acme.sh после нескольких попыток."
        return 1
    fi
    
    cd acme.sh
    
    # Установить
    log "Запуск инсталлятора..."
    if ! retry_cmd ./acme.sh --install -m "$EMAIL"; then
        error "Ошибка запуска инсталлятора acme.sh после нескольких попыток."
        return 1
    fi
    
    # Проверить
    if command -v acme.sh &> /dev/null; then
        success "acme.sh успешно установлен"
        
        # Показать путь
        ACME_HOME=$(acme.sh --help 2>/dev/null | grep "Home:" | awk '{print $3}')
        if [ -z "$ACME_HOME" ]; then
            ACME_HOME="$HOME/.acme.sh"
        fi
        info "ACME Home: $ACME_HOME"
        
        return 0
    else
        error "Ошибка установки acme.sh"
        return 1
    fi
}

configure_duckdns_token() {
    local token=$1
    
    log "Конфигурация DuckDNS TOKEN для acme.sh..."
    
    # Проверить существование config файла acme.sh
    if [ ! -f "$ACME_HOME/account.conf" ]; then
        touch "$ACME_HOME/account.conf"
    fi
    
    # Добавить или обновить токен
    # sed -i.bak "s|export DuckDNS_Token=.*|export DuckDNS_Token=\"$token\"|" "$ACME_HOME/account.conf" is not idempotent, so needs manual check before using retry
    
    # Use a temporary file for atomic update
    local temp_acme_conf=$(mktemp)
    if grep -q "DuckDNS_Token" "$ACME_HOME/account.conf"; then
        sed "s|export DuckDNS_Token=.*|export DuckDNS_Token=\"$token\"|" "$ACME_HOME/account.conf" > "$temp_acme_conf"
    else
        cat "$ACME_HOME/account.conf" > "$temp_acme_conf"
        echo "export DuckDNS_Token=\"$token\"" >> "$temp_acme_conf"
    fi

    if ! mv "$temp_acme_conf" "$ACME_HOME/account.conf"; then
        error "Не удалось обновить файл конфигурации acme.sh DuckDNS токеном."
        rm "$temp_acme_conf" # Clean up temp file
        return 1
    fi
    
    chmod 600 "$ACME_HOME/account.conf"
    success "DuckDNS_Token сконфигурирован"
}

issue_certificate() {
    local domain=$1
    local email=$2
    
    separator
    log "Получение SSL сертификата через Let's Encrypt..."
    log "  Domain: $domain"
    log "  Email: $email"
    
    export DuckDNS_Token="$DUCKDNS_TOKEN"
    
    # Основной домен + wildcard
    if retry_cmd acme.sh --issue \
        --dns dns_duckdns \
        -d "$domain" \
        -d "*.$domain" \
        --email "$email" \
        --ecc \
        --dnssleep 120 \
        2>&1 | tee -a "$MAIN_LOG"; then
        success "Сертификат успешно получен"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Сертификат получен для $domain" >> "$SSL_LOG"
        return 0
    else
        error "Ошибка получения сертификата после нескольких попыток."
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Ошибка: Не удалось получить сертификат после нескольких попыток." >> "$SSL_LOG"
        return 1
    fi
}

verify_certificate() {
    local domain=$1
    
    log "Проверка сертификата..."
    
    local cert_path="$ACME_HOME/${domain}_ecc/fullchain.cer"
    
    if [ ! -f "$cert_path" ]; then
        error "Сертификат не найден: $cert_path"
        echo "NOT_FOUND" # Indicate not found
        return 1
    fi
    
    # Получить дату истечения в формате UTC и Unix timestamp
    local expiry_date_str=$(openssl x509 -enddate -noout -in "$cert_path" 2>/dev/null | cut -d= -f2)
    
    if [ -z "$expiry_date_str" ]; then
        error "Не удалось получить информацию о сертификате"
        echo "ERROR" # Indicate error
        return 1
    fi

    # Convert expiry_date_str to a format date -d can understand
    # Example: 'May 20 12:00:00 2026 GMT' -> '2026-05-20 12:00:00 GMT'
    # This requires GNU date or compatible.
    # We will assume GNU date or compatible.
    local expiry_timestamp=$(date -d "$expiry_date_str" +%s)
    local current_timestamp=$(date +%s)

    local seconds_remaining=$((expiry_timestamp - current_timestamp))
    local days_remaining=$((seconds_remaining / 86400)) # 86400 seconds in a day
    
    success "Сертификат найден"
    info "Срок действия: $expiry_date_str"
    info "Осталось дней: $days_remaining"
    
    # Показать CN и Subject Alt Names
    info "Subject:"
    openssl x509 -noout -subject -in "$cert_path" | sed 's/subject=/  /'
    
    echo "$expiry_date_str|$days_remaining" # Return expiry info
    return 0
}

check_certificate_renewal() {
    local domain=$1
    local email=$2
    
    separator
    log "Проверка статуса сертификата для автоматического обновления..."
    
    local cert_info=$(verify_certificate "$domain")
    local verify_status=$?

    if [ "$verify_status" -ne 0 ]; then
        error "Не удалось получить информацию о сертификате для $domain. Возможно, сертификат отсутствует или поврежден."
        # Attempt to issue a new certificate if not found
        if [[ "$cert_info" == "NOT_FOUND" ]]; then
            warning "Сертификат для $domain не найден. Попытка получить новый сертификат."
            if issue_certificate "$domain" "$email"; then
                success "Новый сертификат для $domain успешно получен."
                return 0
            else
                error "Не удалось получить новый сертификат для $domain."
                return 1
            fi
        fi
        return 1
    fi

    local days_remaining=$(echo "$cert_info" | awk -F'|' '{print $2}')

    if [ -z "$days_remaining" ]; then
        error "Не удалось определить количество дней до истечения срока действия сертификата для $domain."
        return 1
    fi

    if [ "$days_remaining" -le "$DAYS_TO_RENEWAL" ]; then
        warning "Сертификат для $domain истекает через $days_remaining дней. Запускаю обновление..."
        if retry_cmd acme.sh --renew -d "$domain" --ecc; then
            success "Сертификат для $domain успешно обновлен."
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Сертификат обновлен для $domain" >> "$SSL_LOG"
            return 0
        else
            error "Не удалось обновить сертификат для $domain после нескольких попыток."
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Ошибка: Не удалось обновить сертификат для $domain." >> "$SSL_LOG"
            return 1
        fi
    else
        success "Сертификат для $domain действителен еще $days_remaining дней. Обновление не требуется."
        return 0
    fi
}

install_cronjob() {
    log "Установка автоматического обновления через cron..."
    
    # acme.sh сама устанавливает cron при установке
    # Проверить, установлена ли
    if acme.sh --list-cron 2>/dev/null | grep -q "cron"; then
        success "Cron для acme.sh уже установлен"
    else
        if retry_cmd acme.sh --install-cronjob; then
            success "Cron для acme.sh установлен"
        else
            error "Не удалось установить cron для acme.sh после нескольких попыток."
            return 1
        fi
    fi
}

# ============================================================================ 
#                   ФУНКЦИИ РАБОТЫ С IP ОБНОВЛЕНИЕМ
# ============================================================================ 

create_ip_update_script() {
    local script_path="/usr/local/bin/update-duckdns-ip.sh"
    
    log "Создание скрипта обновления IP..."
    
    cat > "$script_path" << 'EOFSCRIPT'
#!/bin/bash

# Загрузить конфигурацию
if [ ! -f "$HOME/.auto-setup-config/config.env" ]; then
    echo "Конфигурационный файл не найден"
    exit 1
fi

source "$HOME/.auto-setup-config/config.env"

# Получить текущий IP
PUBLIC_IP=""
if [ -z "$PUBLIC_IP" ]; then # No need for retry_cmd here, dig has built-in retry
    PUBLIC_IP=$(dig +short myip.opendns.com @resolver1.opendns.com 2>/dev/null)
fi

if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP=$(curl -s ipinfo.io/ip)
fi

if [ -z "$PUBLIC_IP" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Не удалось получить IP" >> "$IP_LOG"
    exit 1
fi

# Проверить формат IP
if [[ ! $PUBLIC_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Некорректный IP: $PUBLIC_IP" >> "$IP_LOG"
    exit 1
fi

LAST_KNOWN_IP=""
if [ -f "$LAST_KNOWN_IP_FILE" ]; then
    LAST_KNOWN_IP=$(cat "$LAST_KNOWN_IP_FILE")
fi

if [ "$PUBLIC_IP" = "$LAST_KNOWN_IP" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️ IP не изменился: $FULL_DOMAIN -> $PUBLIC_IP" >> "$IP_LOG"
    exit 0
fi

# Отправить на DuckDNS
RESPONSE=$(curl -s "https://www.duckdns.org/update?domains=$DOMAIN_NAME&token=$DUCKDNS_TOKEN&ip=$PUBLIC_IP")

if [[ "$RESPONSE" == *"OK"* ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ IP обновлен: $FULL_DOMAIN -> $PUBLIC_IP" >> "$IP_LOG"
    echo "$PUBLIC_IP" > "$LAST_KNOWN_IP_FILE" # Save last known IP
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Ошибка: $RESPONSE" >> "$IP_LOG"
    exit 1
fi
EOFSCRIPT
    
    chmod +x "$script_path"
    success "Скрипт обновления IP создан: $script_path"
}

install_ip_cronjob() {
    local script_path="/usr/local/bin/update-duckdns-ip.sh"
    
    log "Установка cron для обновления IP (каждые 5 минут)..."
    
    # Временный файл для crontab
    local temp_cron=$(mktemp)
    
    # Получить текущие cron задачи (кроме старых от этого скрипта)
    crontab -l 2>/dev/null | grep -v "update-duckdns-ip" > "$temp_cron" || true
    
    # Добавить новую задачу
    echo "*/5 * * * * $script_path >> /var/log/auto-setup/cron.log 2>&1" >> "$temp_cron"
    
    # Установить обновленный crontab
    if retry_cmd crontab "$temp_cron"; then
        success "Cron для обновления IP установлен"
        log "Скрипт будет запускаться каждые 5 минут"
    else
        error "Не удалось установить cron для обновления IP после нескольких попыток."
        return 1
    fi
    rm "$temp_cron"
}

# ============================================================================ 
#                   ФУНКЦИИ КОНФИГУРАЦИИ ВЕБ-СЕРВЕРА
# ============================================================================ 

setup_nginx() {
    local domain=$1
    local port=$2
    
    separator
    log "Конфигурация Nginx..."
    
    # Проверить установку Nginx
    if ! command -v nginx &> /dev/null; then
        log "Установка Nginx..."
        if command -v apt-get &> /dev/null; then
            if ! retry_cmd apt-get update; then
                error "Не удалось обновить apt-get после нескольких попыток."
                return 1
            fi
            if ! retry_cmd apt-get install -y nginx; then
                error "Не удалось установить Nginx через apt-get после нескольких попыток."
                return 1
            fi
        elif command -v yum &> /dev/null; then
            if ! retry_cmd yum install -y nginx; then
                error "Не удалось установить Nginx через yum после нескольких попыток."
                return 1
            fi
        else
            warning "Не удалось автоматически установить Nginx"
            return 1
        fi
    fi
    
    # Создать конфигурацию
    local config_file="/etc/nginx/sites-available/$domain.conf"
    
    cat > "$config_file" << EOFNGINX
# Автоматически сгенерирована $(date)

upstream app_backend {
    server localhost:$port;
}

server {
    listen 80 default_server;
    server_name $domain;
    
    # Перенаправление на HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2 default_server;
    server_name $domain *.${domain};
    
    # Пути к сертификатам
    ssl_certificate $ACME_HOME/${domain}_ecc/fullchain.cer;
    ssl_certificate_key $ACME_HOME/${domain}_ecc/${domain}.key;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Другие заголовки безопасности
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Логирование
    access_log /var/log/nginx/${domain}_access.log;
    error_log /var/log/nginx/${domain}_error.log;
    
    # Проксирование
    location / {
        proxy_pass http://app_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # WebSocket поддержка
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOFNGINX
    
    success "Nginx конфигурация создана: $config_file"
    
    # Включить сайт
    if [ ! -L "/etc/nginx/sites-enabled/$domain.conf" ]; then
        ln -s "/etc/nginx/sites-available/$domain.conf" "/etc/nginx/sites-enabled/$domain.conf"
        success "Сайт включен в sites-enabled"
    fi
    
    # Проверить синтаксис
    if retry_cmd nginx -t; then
        success "Синтаксис Nginx корректен"
        
        # Перезагрузить Nginx
        if retry_cmd systemctl restart nginx; then
            success "Nginx перезагружен"
        else
            error "Не удалось перезагрузить Nginx после нескольких попыток."
            return 1
        fi
    else
        error "Ошибка синтаксиса в конфигурации Nginx"
        return 1
    fi
}

setup_apache() {
    local domain=$1
    local port=$2
    
    separator
    log "Конфигурация Apache..."
    
    # Проверить установку Apache
    if ! command -v apache2ctl &> /dev/null && ! command -v apachectl &> /dev/null; then
        log "Установка Apache..."
        if command -v apt-get &> /dev/null; then
            if ! retry_cmd apt-get update; then
                error "Не удалось обновить apt-get после нескольких попыток."
                return 1
            fi
            if ! retry_cmd apt-get install -y apache2; then
                error "Не удалось установить Apache через apt-get после нескольких попыток."
                return 1
            fi
        elif command -v yum &> /dev/null; then
            if ! retry_cmd yum install -y httpd; then
                error "Не удалось установить Apache через yum после нескольких попыток."
                return 1
            fi
        fi
    fi
    
    # Включить нужные модули
    retry_cmd a2enmod ssl 2>/dev/null || true
    retry_cmd a2enmod rewrite 2>/dev/null || true
    retry_cmd a2enmod proxy 2>/dev/null || true
    retry_cmd a2enmod proxy_http 2>/dev/null || true
    
    # Создать конфигурацию
    local config_file="/etc/apache2/sites-available/${domain}-ssl.conf"
    
    cat > "$config_file" << EOFAPACHE
# Автоматически сгенерирована $(date)

<VirtualHost *:80>
    ServerName $domain
    ServerAlias *.$domain
    
    # Перенаправление на HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName $domain
    ServerAlias *.$domain
    
    # SSL Сертификаты
    SSLEngine on
    SSLCertificateFile $ACME_HOME/${domain}_ecc/fullchain.cer
    SSLCertificateKeyFile $ACME_HOME/${domain}_ecc/${domain}.key
    
    # SSL настройки
    SSLProtocol TLSv1.2 TLSv1.3
    SSLCipherSuite HIGH:!aNULL:!MD5
    SSLHonorCipherOrder on
    
    # HSTS
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # Другие заголовки
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    
    # Логирование
    CustomLog /var/log/apache2/${domain}_access.log combined
    ErrorLog /var/log/apache2/${domain}_error.log
    
    # Проксирование
    ProxyPreserveHost On
    ProxyPass / http://localhost:$port/ nocanon
    ProxyPassReverse / http://localhost:$port/
    
    # WebSocket поддержка
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:$port/\$1" [P,L]
</VirtualHost>
EOFAPACHE
    
    success "Apache конфигурация создана: $config_file"
    
    # Включить сайт
    retry_cmd a2ensite "${domain}-ssl" 2>/dev/null || true
    
    # Проверить синтаксис
    if retry_cmd apache2ctl configtest; then
        success "Синтаксис Apache корректен"
        
        # Перезагрузить Apache
        if retry_cmd systemctl restart apache2; then
            success "Apache перезагружен"
        else
            error "Не удалось перезагрузить Apache после нескольких попыток."
            return 1
        fi
    else
        warning "Проверьте конфигурацию Apache вручную"
    fi
}

# ============================================================================ 
#                        ГЛАВНЫЙ ПРОЦЕСС УСТАНОВКИ
# ============================================================================ 

main() {
    separator
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  УНИВЕРСАЛЬНЫЙ СКРИПТ АВТОМАТИЗАЦИИ DNS + SSL             ║"
    echo "║  DuckDNS + acme.sh + Let's Encrypt                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    separator
    
    # 1. Проверки
    log "=== ЭТАП 1: ПРОВЕРКИ ==="
    check_root
    check_dependencies
    
    # 2. Конфигурация
    log "=== ЭТАП 2: КОНФИГУРАЦИЯ ==="
    create_config
    load_config
    
    # 3. Проверка DuckDNS TOKEN
    log "=== ЭТАП 3: ПРОВЕРКА DuckDNS ==="
    
    if [ "$DUCKDNS_TOKEN" = "AUTO_GENERATE" ]; then
        error "Автоматическая регистрация в DuckDNS пока требует ручной регистрации"
        echo
        echo -e "${YELLOW}Пожалуйста выполните следующие шаги вручную:${NC}"
        echo "  1. Перейдите на https://www.duckdns.org/"
        echo "  2. Залогиньтесь через GitHub/Google"
        echo "  3. Добавьте домен: $DOMAIN_NAME"
        echo "  4. Скопируйте ваш TOKEN с верхней части страницы"
        echo "  5. Вставьте его ниже"
        echo
        
        read -p "Введите ваш DuckDNS TOKEN: " DUCKDNS_TOKEN
        
        if [ -z "$DUCKDNS_TOKEN" ]; then
            error "TOKEN не может быть пустым"
            exit 1
        fi
        
        # Обновить конфигурацию
        sed -i.bak "s|export DUCKDNS_TOKEN=.*|export DUCKDNS_TOKEN=\"$DUCKDNS_TOKEN\"|" "$CONFIG_FILE"
        source "$CONFIG_FILE"
    fi
    
    # Проверить TOKEN
    if ! test_duckdns_token "$DUCKDNS_TOKEN"; then
        error "DuckDNS TOKEN невалиден. Проверьте его и попробуйте снова"
        exit 1
    fi
    
    # 4. Получение и обновление IP
    log "=== ЭТАП 4: РАБОТА С IP АДРЕСОМ ==="
    
    PUBLIC_IP=$(get_public_ip)
    if [ $? -ne 0 ]; then # Check exit code of get_public_ip
        error "Не удалось получить корректный IP адрес"
        exit 1
    fi
    
    if ! verify_ip "$PUBLIC_IP"; then
        error "Не удалось получить корректный IP адрес: $PUBLIC_IP"
        exit 1
    fi
    success "Публичный IP: $PUBLIC_IP"
    
    if ! update_duckdns "$DUCKDNS_TOKEN" "$DOMAIN_NAME" "$PUBLIC_IP"; then
        error "Ошибка обновления DuckDNS"
        exit 1
    fi
    
    # Подождать распространения DNS
    log "Ожидание распространения DNS (30 секунд)..."
    sleep 30
    
    # Проверить DNS
    if verify_dns "$FULL_DOMAIN"; then
        success "DNS проверка прошла успешно"
    else
        warning "DNS еще не распространился, но мы продолжаем..."
    fi
    
    # 5. Установка acme.sh
    log "=== ЭТАП 5: УСТАНОВКА ACME.SH ==="
    
    if ! install_acme; then
        error "Ошибка установки acme.sh"
        exit 1
    fi
    
    # Загрузить актуальный ACME_HOME
    ACME_HOME="$HOME/.acme.sh"
    
    # Конфигурация токена
    configure_duckdns_token "$DUCKDNS_TOKEN"
    
    # 6. Получение сертификата
    log "=== ЭТАП 6: ПОЛУЧЕНИЕ SSL СЕРТИФИКАТА ==="
    
    if ! issue_certificate "$FULL_DOMAIN" "$EMAIL"; then
        error "Ошибка получения сертификата"
        error "Проверьте логи: $MAIN_LOG"
        exit 1
    fi
    
    # Верификация и проверка на обновление сертификата
    if ! check_certificate_renewal "$FULL_DOMAIN" "$EMAIL"; then
        error "Проверка и/или обновление сертификата завершились с ошибкой."
        exit 1
    fi
    
    # 7. Установка cron для автоматизации
    log "=== ЭТАП 7: АВТОМАТИЗАЦИЯ ==="
    
    install_cronjob  # Для автоматического обновления сертификата
    create_ip_update_script
    install_ip_cronjob  # Для автоматического обновления IP
    
    # 8. Конфигурация веб-сервера
    if [ "$WEB_SERVER" = "nginx" ]; then
        setup_nginx "$FULL_DOMAIN" "$APP_PORT"
    elif [ "$WEB_SERVER" = "apache" ]; then
        setup_apache "$FULL_DOMAIN" "$APP_PORT"
    else
        info "Конфигурация веб-сервера пропущена"
    fi
    
    # 9. Финальная информация
    separator
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
    echo "║  ✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО                          ║"
    echo "╚════════════════════════════════════════════════════════════╝${NC}"
    separator
    
    echo
    echo -e "${CYAN}=== ИНФОРМАЦИЯ О СИСТЕМЕ ===${NC}"
    echo -e "  ${GREEN}Домен${NC}: $FULL_DOMAIN"
    echo -e "  ${GREEN}IP адрес${NC}: $PUBLIC_IP"
    echo -e "  ${GREEN}Email${NC}: $EMAIL"
    echo -e "  ${GREEN}Порт приложения${NC}: $APP_PORT"
    echo -e "  ${GREEN}Веб-сервер${NC}: $WEB_SERVER"
    echo
    echo -e "${CYAN}=== ПУТИ И ФАЙЛЫ ===${NC}"
    echo -e "  ${GREEN}Конфигурация${NC}: $CONFIG_FILE"
    echo -e "  ${GREEN}Логи${NC}: $LOG_DIR"
    echo -e "  ${GREEN}ACME Home${NC}: $ACME_HOME"
    echo
    echo -e "${CYAN}=== СЕРТИФИКАТЫ ===${NC}"
    cert_path="$ACME_HOME/${FULL_DOMAIN}_ecc"
    echo -e "  ${GREEN}Основной сертификат${NC}: $cert_path/fullchain.cer"
    echo -e "  ${GREEN}Приватный ключ${NC}: $cert_path/${FULL_DOMAIN}.key"
    echo
    echo -e "${CYAN}=== АВТОМАТИЗАЦИЯ ===${NC}"
    echo -e "  ${GREEN}Обновление IP${NC}: каждые 5 минут (cron)"
    echo -e "  ${GREEN}Обновление сертификата${NC}: автоматическое (acme.sh cron)"
    echo -e "  ${GREEN}Скрипт обновления IP${NC}: /usr/local/bin/update-duckdns-ip.sh"
    echo
    echo -e "${CYAN}=== ПРОВЕРКИ И КОМАНДЫ ===${NC}"
    echo -e "  ${GREEN}Проверить DNS${NC}: dig $FULL_DOMAIN"
    echo -e "  ${GREEN}Проверить сертификат${NC}: openssl x509 -in $cert_path/fullchain.cer -noout -dates"
    echo -e "  ${GREEN}Посмотреть cron${NC}: crontab -l"
    echo -e "  ${GREEN}Посмотреть логи${NC}: tail -f $MAIN_LOG"
    echo -e "  ${GREEN}Проверить HTTPS${NC}: curl -I https://$FULL_DOMAIN:443/"
    echo
    
    # Подсказка по следующим шагам
    if [ "$WEB_SERVER" = "none" ]; then
        echo -e "${YELLOW}⚠️  Веб-сервер не был конфигурирован${NC}"
        echo -e "  Используйте сертификаты для собственного приложения:"
        echo -e "  • Сертификат: $cert_path/fullchain.cer"
        echo -e "  • Ключ: $cert_path/${FULL_DOMAIN}.key"
        echo
    fi
    
    separator
    success "Для просмотра логов: tail -f $MAIN_LOG"
    success "Для перезагрузки конфигурации: source $CONFIG_FILE"
    echo
}

# ============================================================================ 
#                            ЗАПУСК
# ============================================================================ 

# Обработка аргументов
case "${1:-}" in
    "config")
        check_root
        create_config
        ;;
    "status")
        load_config
        log "=== СТАТУС СИСТЕМЫ ==="
        echo
        echo "Конфигурация:"
        source "$CONFIG_FILE"
        grep "^export " "$CONFIG_FILE" | sed 's/export /  • /'
        echo
        
        echo "Публичный IP:"
        ip=$(get_public_ip)
        echo "  $ip"
        echo
        
        if command -v acme.sh &> /dev/null; then
            echo "Сертификаты:"
            acme.sh --list | tail -n +2
        fi
        echo
        ;;
    "renew")
        load_config
        log "Запуск ручного обновления сертификата..."
        if ! check_certificate_renewal "$FULL_DOMAIN" "$EMAIL"; then
            error "Ручное обновление сертификата завершилось с ошибкой."
            exit 1
        fi
        ;;
    "logs")
        tail -f "$MAIN_LOG"
        ;;
    "ip-logs")
        tail -f "$IP_LOG"
        ;;
    "test")
        load_config
        log "=== ПРОВЕРКА КОМПОНЕНТОВ ==="
        
        # Проверить IP
        echo
        log "1. Проверка IP..."
        ip=$(get_public_ip)
        if [ $? -ne 0 ]; then # Check exit code of get_public_ip
            error "Не удалось получить корректный IP адрес"
        elif verify_ip "$ip"; then
            success "IP: $ip ✓"
        else
            error "IP: $ip ✗"
        fi
        
        # Проверить DNS
        echo
        log "2. Проверка DNS..."
        if verify_dns "$FULL_DOMAIN"; then
            success "DNS: $FULL_DOMAIN ✓"
        else
            warning "DNS: еще не распространился"
        fi
        
        # Проверить сертификат
        echo
        log "3. Проверка сертификата..."
        local cert_status=$(verify_certificate "$FULL_DOMAIN")
        if [ $? -eq 0 ]; then
            success "Сертификат ✓"
            # Optional: parse cert_status for more info
        else
            error "Сертификат ✗"
        fi
        
        # Проверить cron
        echo
        log "4. Проверка cron..."
        if crontab -l 2>/dev/null | grep -q "acme.sh"; then
            success "ACME cron ✓"
        else
            warning "ACME cron не установлен"
        fi
        
        if crontab -l 2>/dev/null | grep -q "update-duckdns-ip"; then
            success "IP cron ✓"
        else
            warning "IP cron не установлен"
        fi
        ;;
    "help"|"-h"|"--help")
        cat << 'EOFHELP'
ИСПОЛЬЗОВАНИЕ: ./auto-setup.sh [КОМАНДА]

КОМАНДЫ:
  (пусто)     Запуск полной установки
  config      Создание/редактирование конфигурации
  status      Показать текущий статус системы
  renew       Обновить сертификат вручную
  logs        Просмотр основных логов
  ip-logs     Просмотр логов обновления IP
  test        Проверить все компоненты
  help        Показать эту справку

ПРИМЕРЫ:
  sudo ./auto-setup.sh              # Запуск установки
  sudo ./auto-setup.sh config       # Редактирование конфигурации
  sudo ./auto-setup.sh status       # Проверить статус
  ./auto-setup.sh test              # Протестировать систему
  tail -f /var/log/auto-setup/setup.log  # Просмотр логов

ЛОГИ:
  /var/log/auto-setup/setup.log     Основной лог установки
  /var/log/auto-setup/ip-updates.log    Логи обновления IP
  /var/log/auto-setup/ssl-updates.log   Логи обновления SSL

КОНФИГУРАЦИЯ:
  ~/.auto-setup-config/config.env   Файл конфигурации

ФАЙЛЫ:
  ~/.acme.sh/                       Директория acme.sh
  /etc/nginx/sites-available/       Конфигурация Nginx
  /etc/apache2/sites-available/     Конфигурация Apache
EOFHELP
        ;;
    *)
        main "$@"
        ;;
esac