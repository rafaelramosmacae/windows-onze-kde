/*
 * Onze — botão "Task View" (abre a Visão geral do KWin)
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
    Plasmoid.icon: "view-grid"

    toolTipMainText: i18n("Task View")
    toolTipSubText: i18n("Shows all windows and virtual desktops")

    function launch() {
        executable.exec("dbus-send --session --type=method_call --dest=org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut string:'Overview'")
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
        activeFocusOnTab: true
        Accessible.name: i18n("Task View")
        Accessible.role: Accessible.Button

        readonly property real side: Kirigami.Units.iconSizes.medium + Kirigami.Units.largeSpacing
        Layout.minimumWidth: root.vertical ? 0 : side
        Layout.maximumWidth: root.vertical ? Infinity : side
        Layout.minimumHeight: root.vertical ? side : 0
        Layout.maximumHeight: root.vertical ? side : Infinity
        Layout.fillHeight: !root.vertical
        Layout.fillWidth: root.vertical

        onClicked: root.launch()
        Keys.onReturnPressed: root.launch()
        Keys.onSpacePressed: root.launch()

        Rectangle {
            visible: area.containsMouse || area.activeFocus
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing / 2
            radius: Kirigami.Units.cornerRadius
            readonly property color fg: Kirigami.Theme.textColor
            color: Qt.rgba(fg.r, fg.g, fg.b, area.pressed ? 0.04 : 0.06)
        }

        Kirigami.Icon {
            anchors.centerIn: parent
            width: Kirigami.Units.iconSizes.smallMedium
            height: width
            source: "view-grid"
            fallback: "window"
            scale: area.pressed ? 0.9 : 1
            Behavior on scale { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }
    }
}
