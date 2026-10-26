import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_iconOnly: iconOnly.checked

    Kirigami.FormLayout {
        QQC2.CheckBox {
            id: iconOnly
            Kirigami.FormData.label: i18n("Appearance:")
            text: i18n("Show only the icon (like the \"Search icon only\" option in Windows)")
        }
    }
}
