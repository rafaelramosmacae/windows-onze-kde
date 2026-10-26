/*
 * Onze — disposição da área de trabalho no estilo Windows 11
 *
 *   [ espaço ][ Iniciar | Pesquisar | Visão de tarefas | apps fixados ][ espaço ][ bandeja | relógio | ▏]
 *
 * Os dois espaçadores flexíveis centralizam o grupo do meio, como na
 * barra de tarefas do Windows 11.
 */

// Taskbar alignment: "center" (Windows 11 default) or "left" (Windows 10 style).
// install.sh rewrites this value according to the user's choice.
var startAlignment = "center";

// Start button icon. install.sh replaces it with "onze-start-here", an identical
// copy of the Win11 pack's 32 px Start logo, so it is the same at any taskbar height.
var startIcon = "start-here-kde-plasma";

// --- Área de trabalho --------------------------------------------------------
// Desktop icon size: 0 = 22px, 1 = 32px, 2 = 48px, 3 = 64px (Plasma default), 4 = 96px...
// install.sh rewrites this value (default 2 = 48px, one level below Plasma's default).
var desktopIconSize = 2;

var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = "org.kde.image";
    desktopsArray[j].currentConfigGroup = ["General"];
    desktopsArray[j].writeConfig("iconSize", desktopIconSize);
    // icons in columns, top to bottom, ordered by date (Home, then Trash), as in Windows
    desktopsArray[j].writeConfig("arrangement", 1);
    desktopsArray[j].writeConfig("sortMode", 4);
}

// --- Barra de tarefas -------------------------------------------------------------
var panel = new Panel;
panel.location = "bottom";
panel.height = 40;                                  // altura da barra (px)
panel.hiding = "none";
try { panel.floating = false; } catch (e) { /* versões antigas */ }
try { panel.lengthMode = "fill"; } catch (e) {}

// Torna a barra opaca ao maximizar (como no Windows 11) quando suportado
try { panel.opacity = "adaptive"; } catch (e) {}

function hasPlugin(id) {
    try {
        return knownWidgetTypes.indexOf(id) !== -1;
    } catch (e) {
        return true;
    }
}

function add(id) {
    if (!hasPlugin(id)) {
        print("Onze: plasmoid ausente, ignorando " + id);
        return null;
    }
    return panel.addWidget(id);
}

// Espaçador da esquerda (flexível) — só no modo centralizado
if (startAlignment !== "left") {
    add("org.kde.plasma.panelspacer");
}

// Menu Iniciar (Kickoff)
var kickoff = add("org.kde.plasma.kickoff");
if (kickoff) {
    kickoff.currentConfigGroup = ["Shortcuts"];
    kickoff.writeConfig("global", "Alt+F1");
    kickoff.currentConfigGroup = ["General"];
    kickoff.writeConfig("icon", startIcon);
    kickoff.writeConfig("favoritesDisplay", 0);          // fixados em grade
    kickoff.writeConfig("applicationsDisplay", 1);       // "Todos os apps" em lista
    kickoff.writeConfig("showActionButtonCaptions", false);
    kickoff.writeConfig("switchCategoryOnHover", false);
    kickoff.writeConfig("highlightNewlyInstalledApps", true);
}

// Caixa "Pesquisar" (abre o KRunner) e botão "Visão de tarefas"
add("org.kde.onze.search");
add("org.kde.onze.taskview");

// Gerenciador de tarefas somente com ícones
var tasks = add("org.kde.plasma.icontasks");
if (tasks) {
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("launchers", [
        "applications:org.kde.dolphin.desktop",
        "preferred://browser",
        "applications:org.kde.discover.desktop",
        "applications:org.kde.konsole.desktop",
        "applications:systemsettings.desktop"
    ].join(","));
    tasks.writeConfig("fill", false);
    tasks.writeConfig("iconSpacing", 1);
    tasks.writeConfig("maxStripes", 1);
    tasks.writeConfig("groupingStrategy", 1);
    tasks.writeConfig("indicateAudioStreams", true);
    tasks.writeConfig("showOnlyCurrentDesktop", true);
}

// Espaçador da direita (flexível)
add("org.kde.plasma.panelspacer");

// Bandeja do sistema
add("org.kde.plasma.systemtray");

// Relógio: hora sobre a data
var clock = add("org.kde.plasma.digitalclock");
if (clock) {
    clock.currentConfigGroup = ["Appearance"];
    clock.writeConfig("showDate", true);
    clock.writeConfig("dateFormat", "shortDate");
    clock.writeConfig("dateDisplayFormat", 2);   // abaixo da hora
    clock.writeConfig("showSeconds", 0);
    // fonte menor e fixa, como no Windows 11 (padrão do Plasma é automático e grande)
    clock.writeConfig("autoFontAndSize", false);
    clock.writeConfig("fontSize", 10);
    clock.writeConfig("fontWeight", 400);
}

// Faixa "Mostrar área de trabalho" no canto direito
add("org.kde.onze.showdesktop");
