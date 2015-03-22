//
//  FirstViewController.h
//  BlueToothLETest
//
//  Created by Kurt Schaefer on 4/13/14.
//  Copyright (c) 2014 Kurt Schaefer. All rights reserved.
//

#import <UIKit/UIKit.h>
#import <CoreBluetooth/CoreBluetooth.h>
#import "UARTPeripheral.h"


@interface JogViewController : UIViewController <CBCentralManagerDelegate, UARTPeripheralDelegate>

@end
