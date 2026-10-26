/*
 * Onze — faixa "Show Desktop" no canto da barra de tarefas
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.icon: "user-desktop"

    toolTipMainText: i18n("Show Desktop")
    toolTipSubText: i18n("Minimizes or restores all windows")

    function toggle() {
        executable.exec("dbus-send --session --type=method_call --dest=org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut string:'Show Desktop'")
    }

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => disconnectSource(sourceName)
        function exec(cmd) {
            connectSource(cmd)
        }
    }

    fullRepresentation: MouseArea {
        id: area
        hoverEnabled: true
        Accessible.name: i18n("Show Desktop")
        Accessible.role: Accessible.Button

        readonly property real thickness: Kirigami.Units.smallSpacing * 3
        Layout.minimumWidth: root.vertical ? 0 : thickness
        Layout.maximumWidth: root.vertical ? Infinity : thickness
        Layout.minimumHeight: root.vertical ? thickness : 0
        Layout.maximumHeight: root.vertical ? thickness : Infinity
        Layout.fillHeight: !root.vertical
        Layout.fillWidth: root.vertical

        onClicked: root.toggle()

        readonly property color fg: Kirigami.Theme.textColor

        // linha divisória fina (como no Windows 11)
        Rectangle {
            x: root.vertical ? Kirigami.Units.smallSpacing : 0
            y: root.vertical ? 0 : Kirigami.Units.smallSpacing
            width: root.vertical ? parent.width - Kirigami.Units.smallSpacing * 2 : 1
            height: root.vertical ? 1 : parent.height - Kirigami.Units.smallSpacing * 2
            color: Qt.rgba(area.fg.r, area.fg.g, area.fg.b, 0.25)
        }

        Rectangle {
            anchors.fill: parent
            anchors.leftMargin: root.vertical ? 0 : 1
            anchors.topMargin: root.vertical ? 1 : 0
            color: Qt.rgba(area.fg.r, area.fg.g, area.fg.b, area.pressed ? 0.12 : 0.07)
            visible: area.containsMouse
        }
    }
}
